import shutil
import tempfile
from unittest import skipUnless

from django import forms
from django.contrib.sites.models import Site
from django.core.exceptions import ImproperlyConfigured
from django.core.files.uploadedfile import SimpleUploadedFile
from django.template import RequestContext
from django.test.utils import override_settings
from django.urls import reverse
from django.utils.html import escape
from django.utils.timezone import now

from mezzanine.conf import settings
from mezzanine.core.models import CONTENT_STATUS_PUBLISHED
from mezzanine.forms import fields
from mezzanine.forms.forms import FormForForm
from mezzanine.forms.models import FieldEntry, Form, FormEntry
from mezzanine.utils.sites import override_current_site_id
from mezzanine.utils.tests import TestCase


class TestsForm(TestCase):
    def test_forms(self):
        """
        Simple 200 status check against rendering and posting to forms
        with both optional and required fields.
        """
        for required in (True, False):
            form = Form.objects.create(title="Form", status=CONTENT_STATUS_PUBLISHED)
            for (i, (field, _)) in enumerate(fields.NAMES):
                form.fields.create(
                    label="Field %s" % i,
                    field_type=field,
                    required=required,
                    visible=True,
                )
            response = self.client.get(form.get_absolute_url())
            self.assertEqual(response.status_code, 200)
            visible_fields = form.fields.visible()
            data = {"field_%s" % f.id: "test" for f in visible_fields}
            response = self.client.post(form.get_absolute_url(), data=data)
            self.assertEqual(response.status_code, 200)

    @skipUnless(
        settings.USE_MODELTRANSLATION and len(settings.LANGUAGES) > 1,
        "modeltranslation configured for several languages required",
    )
    def test_submit_button_text(self):
        """
        Test that Form.button_text has its value displayed properly without
        being translated back to the default language.
        """
        from collections import OrderedDict

        from django.urls import reverse
        from django.utils.translation import activate, get_language
        from django.utils.translation import gettext as _
        from modeltranslation.utils import auto_populate

        default_language = get_language()
        code_list = OrderedDict(settings.LANGUAGES)
        del code_list[default_language]
        for c in code_list:
            try:
                activate(c)
            except:  # noqa
                pass
            else:
                break
            return
        with auto_populate(True):
            form = Form.objects.create(
                title="Form button_text", status=CONTENT_STATUS_PUBLISHED
            )
            form.fields.create(
                label="Field test", field_type=fields.TEXT, required=True, visible=True
            )
        submit_text = _("Submit")
        form.button_text = submit_text
        form.save()
        # Client session still uses default language
        response = self.client.get(form.get_absolute_url())
        activate(default_language)
        # Default language contains the default translation for Submit
        self.assertContains(response, _("Submit"))
        # Language used for form creation contains its own translation
        self.client.post(reverse("set_language"), data={"language": c})
        response = self.client.get(form.get_absolute_url())
        self.client.post(reverse("set_language"), data={"language": default_language})
        self.assertContains(response, submit_text)

    def test_custom_email_type(self):
        class CustomEmailField(forms.EmailField):
            pass

        fields.CLASSES[16] = CustomEmailField
        fields.NAMES += ((16, "Custom email field"),)

        form_page = Form.objects.create(title="Email form tests")
        form_page.fields.create(label="Email field test", field_type=16)

        test_email = "test@example.com"
        request = self._request_factory.post("/", {"field_1": test_email})

        form = FormForForm(
            form_page,
            RequestContext(request),
            request.POST or None,
            request.FILES or None,
        )

        self.assertTrue(form.is_valid())
        self.assertEqual(form.email_to(), test_email)

    def test_entries_filename_xss(self):
        """
        CVE-2025-29573: uploaded filenames must be escaped in the entries table.
        """
        form = Form.objects.create(title="XSS form", status=CONTENT_STATUS_PUBLISHED)
        field = form.fields.create(
            label="File", field_type=fields.FILE, required=False, visible=True
        )
        entry = FormEntry.objects.create(form=form, entry_time=now())
        filename = '"><img src=x onerror=alert(1)>.pdf'
        FieldEntry.objects.create(
            entry=entry, field_id=field.id, value="forms/abc/%s" % filename
        )
        self.client.login(username=self._username, password=self._password)
        response = self.client.post(
            reverse("admin:form_entries", args=(form.id,)),
            {"field_%s_export" % field.id: "on", "field_0_export": "on"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, filename)
        self.assertContains(response, escape(filename))

    def test_file_view_cross_site_404(self):
        """
        file_view must 404 when the FieldEntry belongs to another site.
        """
        site2 = Site.objects.create(domain="site2.example.com", name="Site 2")
        with override_current_site_id(site2.id):
            form = Form.objects.create(
                title="Other site form", site=site2, status=CONTENT_STATUS_PUBLISHED
            )
            field = form.fields.create(
                label="File", field_type=fields.FILE, required=False, visible=True
            )
            entry = FormEntry.objects.create(form=form, entry_time=now())
            field_entry = FieldEntry.objects.create(
                entry=entry, field_id=field.id, value="forms/abc/secret.pdf"
            )
        self.client.login(username=self._username, password=self._password)
        url = reverse("admin:form_file", args=(field_entry.id,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_field_default_ssti_is_sandboxed(self):
        """
        field.default must not be rendered with RequestContext / settings.
        SSTI payloads must not leak SECRET_KEY or request attributes.
        """
        canary = "super-secret-ssti-canary-key"
        form_page = Form.objects.create(
            title="SSTI form", status=CONTENT_STATUS_PUBLISHED
        )
        field = form_page.fields.create(
            label="Name",
            field_type=fields.TEXT,
            required=False,
            visible=True,
            default=(
                "{{ settings.SECRET_KEY }}"
                "{{ request.user.password }}"
                "{{ request.user.email }}"
            ),
        )
        request = self._request_factory.get("/")
        request.user = self._user
        with override_settings(SECRET_KEY=canary):
            form = FormForForm(form_page, RequestContext(request))
            initial = str(form.initial.get("field_%s" % field.id, ""))
            self.assertNotIn(canary, initial)
            self.assertNotIn(self._user.password, initial)
            # request.user.email is not an allowlisted var
            self.assertNotIn(self._emailaddress, initial)

    def test_field_default_allowlisted_vars(self):
        """Allowlisted sandbox vars user_email, user_name, site_name interpolate."""
        form_page = Form.objects.create(
            title="Prefill form", status=CONTENT_STATUS_PUBLISHED
        )
        field = form_page.fields.create(
            label="Name",
            field_type=fields.TEXT,
            required=False,
            visible=True,
            default="{{ user_email }}|{{ user_name }}|{{ site_name }}",
        )
        request = self._request_factory.get("/")
        request.user = self._user
        form = FormForForm(form_page, RequestContext(request))
        initial = form.initial["field_%s" % field.id]
        self.assertIn(self._emailaddress, initial)
        self.assertIn(self._username, initial)
        self.assertIn(Site.objects.get_current().name, initial)

    def test_upload_rejects_disallowed_extension(self):
        """Disallowed upload extensions must fail form validation."""
        form_page = Form.objects.create(
            title="Upload deny", status=CONTENT_STATUS_PUBLISHED
        )
        field = form_page.fields.create(
            label="File", field_type=fields.FILE, required=True, visible=True
        )
        request = self._request_factory.post("/")
        for name, content, content_type in (
            ("payload.html", b"<script>alert(1)</script>", "text/html"),
            ("malware.exe", b"MZ", "application/octet-stream"),
            ("xss.js", b"alert(1)", "text/javascript"),
            ("image.svg", b"<svg xmlns='http://www.w3.org/2000/svg'></svg>", "image/svg+xml"),
        ):
            uploaded = SimpleUploadedFile(name, content, content_type=content_type)
            form = FormForForm(
                form_page,
                RequestContext(request),
                data={},
                files={"field_%s" % field.id: uploaded},
            )
            self.assertFalse(form.is_valid(), msg="%s should be rejected" % name)
            self.assertIn("field_%s" % field.id, form.errors)

    def test_upload_accepts_allowlisted_extension(self):
        """Allowlisted extensions are stored under FORMS_UPLOAD_ROOT."""
        tmp = tempfile.mkdtemp()
        try:
            with override_settings(FORMS_UPLOAD_ROOT=tmp):
                form_page = Form.objects.create(
                    title="Upload allow", status=CONTENT_STATUS_PUBLISHED
                )
                field = form_page.fields.create(
                    label="File",
                    field_type=fields.FILE,
                    required=True,
                    visible=True,
                )
                uploaded = SimpleUploadedFile(
                    "ok.pdf", b"%PDF-1.4", content_type="application/pdf"
                )
                request = self._request_factory.post("/")
                form = FormForForm(
                    form_page,
                    RequestContext(request),
                    data={},
                    files={"field_%s" % field.id: uploaded},
                )
                self.assertTrue(form.is_valid())
                entry = form.save()
                stored = entry.fields.get(field_id=field.id).value
                self.assertIn("ok.pdf", stored)
        finally:
            shutil.rmtree(tmp)

    def test_empty_forms_upload_root_refused(self):
        """An empty FORMS_UPLOAD_ROOT must not accept uploads."""
        form_page = Form.objects.create(
            title="Empty root", status=CONTENT_STATUS_PUBLISHED
        )
        field = form_page.fields.create(
            label="File", field_type=fields.FILE, required=True, visible=True
        )
        uploaded = SimpleUploadedFile(
            "ok.pdf", b"%PDF-1.4", content_type="application/pdf"
        )
        request = self._request_factory.post("/")
        with override_settings(FORMS_UPLOAD_ROOT=""):
            form = FormForForm(
                form_page,
                RequestContext(request),
                data={},
                files={"field_%s" % field.id: uploaded},
            )
            self.assertTrue(form.is_valid())
            with self.assertRaises(ImproperlyConfigured):
                form.save()
