"""
XSS / sanitize regression suite (Wave 0 / PR-003 + PR-004).

Asserts save-time bleach on RichTextField *and* render of that saved
content under the default RICHTEXT_FILTERS pipeline. Also covers the
two public XSS CVEs already fixed in PR-001 / PR-002:

* CVE-2025-6050 — title-in-JSON served by displayable_links_js
* CVE-2025-29573 — form-upload filename ``"><img…>``

PR-004: default pipeline bleaches on read (after thumbnails).
PR-005b: custom filters that return non-SafeText raise TypeError.
NONE is not in the Setting admin; raw HTML only via NOVA_FORCE_RAW_HTML=1.
"""
import os
import re
from pathlib import Path
from unittest import mock, skipUnless

from bs4 import BeautifulSoup
from django.forms.models import modelform_factory
from django.template import Context, Template
from django.test.utils import override_settings
from django.urls import reverse
from django.utils.html import escape as html_escape
from django.utils.timezone import now

from mezzanine.blog.models import BlogPost
from mezzanine.conf import settings
from mezzanine.core.defaults import RICHTEXT_FILTER_LEVEL_NONE
from mezzanine.core.models import CONTENT_STATUS_PUBLISHED
from mezzanine.forms import fields
from mezzanine.forms.models import FieldEntry, Form, FormEntry
from mezzanine.pages.models import RichTextPage
from mezzanine.utils.html import escape as richtext_escape
from mezzanine.utils.importing import path_for_import
from mezzanine.utils.tests import TestCase


def plain_string_filter(content):
    """Custom RICHTEXT_FILTERS entry that returns a plain str, not SafeText."""
    return "%s" % content


# Payloads that must not survive default HIGH filtering as live markup.
SCRIPT = "<p>ok</p><script>alert(1)</script>"
ONERROR = '<p>ok</p><img src=x onerror=alert(1)>'
JAVASCRIPT_URL = '<p>ok</p><a href="javascript:alert(1)">click</a>'
JAVASCRIPT_URL_CASED = '<p>ok</p><a href="JaVaScRiPt:alert(1)">click</a>'
# Mutation-XSS / <math> vectors that bleach HIGH must neutralize.
MATH_MXSS = (
    "<math><mtext><table><mglyph><style><!--</style>"
    '<img title="--&gt;&lt;img src=1 onerror=alert(1)&gt;">'
)
MATH_SIMPLE = '<math><img src=x onerror=alert(1)></math>'
FILENAME_XSS = '"><img src=x onerror=alert(1)>.pdf'
TITLE_XSS = "</script><script>alert(1)</script>"

# Saved content / |richtext_filters can be checked for tags directly.
# HTTP responses include site chrome (<script src>, comment-reply JS), so
# those checks use payload-specific remnants instead.
LIVE_SCRIPT = ("<script>", "</script>")
LIVE_SCRIPT_ALERT = ("<script>alert",)
# Real <img onerror> only — not the letters "onerror" inside an HTML comment.
LIVE_ONERROR_ATTR = (re.compile(r"<img\b[^>]*\bonerror\b", re.I),)
LIVE_JS_URL = ("javascript:",)
LIVE_MATH = ("<math",)


class SanitizeRegressionTests(TestCase):
    """Save + render XSS regressions under default rich-text filters."""

    def _save_page(self, title, content):
        """Persist a published RichTextPage through ModelForm (field.clean)."""
        form_class = modelform_factory(RichTextPage, fields=["title", "content"])
        form = form_class({"title": title, "content": content})
        self.assertTrue(form.is_valid(), form.errors)
        page = form.save(commit=False)
        page.status = CONTENT_STATUS_PUBLISHED
        page.save()
        return page

    def _save_blog(self, title, content):
        """Persist a published BlogPost through ModelForm (field.clean)."""
        form_class = modelform_factory(BlogPost, fields=["title", "content"])
        form = form_class({"title": title, "content": content})
        self.assertTrue(form.is_valid(), form.errors)
        post = form.save(commit=False)
        post.user = self._user
        post.status = CONTENT_STATUS_PUBLISHED
        post.save()
        return post

    def _render_filters(self, content):
        """Apply the default |richtext_filters pipeline."""
        return Template(
            "{% load mezzanine_tags %}{{ content|richtext_filters }}"
        ).render(Context({"content": content}))

    def _assert_absent(self, html, needles, where):
        for needle in needles:
            if isinstance(needle, re.Pattern):
                self.assertIsNone(
                    needle.search(html),
                    "%s still matches %r: %r" % (where, needle.pattern, html),
                )
            else:
                self.assertNotIn(
                    needle.lower(),
                    html.lower(),
                    "%s still contains %r: %r" % (where, needle, html),
                )

    def _assert_dom_safe(self, html, where):
        """Re-parse like thumbnails()/the browser: no script, math, or on*."""
        soup = BeautifulSoup(html, "html.parser")
        for el in soup.find_all(True):
            name = (el.name or "").lower()
            self.assertNotEqual(
                name, "script", "%s DOM has <script>: %r" % (where, html)
            )
            self.assertNotEqual(name, "math", "%s DOM has <math>: %r" % (where, html))
            for attr in el.attrs or {}:
                self.assertFalse(
                    str(attr).lower().startswith("on"),
                    "%s DOM has %s on <%s>: %r" % (where, attr, name, html),
                )

    def _assert_save_and_render(self, obj, field_needles, page_needles=None):
        """Saved field *and* |richtext_filters *and* HTTP GET are clean."""
        if page_needles is None:
            page_needles = field_needles
        self._assert_absent(obj.content, field_needles, "saved content")
        self._assert_dom_safe(obj.content, "saved content")
        rendered = self._render_filters(obj.content)
        self._assert_absent(rendered, field_needles, "|richtext_filters")
        self._assert_dom_safe(rendered, "|richtext_filters")
        response = self.client.get(obj.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self._assert_absent(
            response.content.decode("utf-8"), page_needles, "HTTP render"
        )

    @skipUnless("mezzanine.pages" in settings.INSTALLED_APPS, "pages app required")
    def test_script_stripped_on_page_save_and_render(self):
        """``<script>`` does not survive RichTextPage save or render."""
        page = self._save_page("Rich text script page", SCRIPT)
        self._assert_save_and_render(page, LIVE_SCRIPT, LIVE_SCRIPT_ALERT)

    @skipUnless("mezzanine.blog" in settings.INSTALLED_APPS, "blog app required")
    def test_script_stripped_on_blog_save_and_render(self):
        """``<script>`` does not survive BlogPost save or render."""
        post = self._save_blog("Rich text script post", SCRIPT)
        self._assert_save_and_render(post, LIVE_SCRIPT, LIVE_SCRIPT_ALERT)

    @skipUnless("mezzanine.pages" in settings.INSTALLED_APPS, "pages app required")
    def test_onerror_stripped_on_save_and_render(self):
        """``onerror`` event handlers do not survive save or render."""
        page = self._save_page("Event handler page", ONERROR)
        self._assert_save_and_render(page, LIVE_ONERROR_ATTR)

    @skipUnless("mezzanine.pages" in settings.INSTALLED_APPS, "pages app required")
    def test_javascript_url_stripped_on_save_and_render(self):
        """``javascript:`` URLs do not survive save or render."""
        page = self._save_page("JS url page", JAVASCRIPT_URL)
        self._assert_save_and_render(page, LIVE_JS_URL)

    @skipUnless("mezzanine.pages" in settings.INSTALLED_APPS, "pages app required")
    def test_javascript_url_case_stripped_on_save_and_render(self):
        """Protocol checks are case-insensitive (``JaVaScRiPt:``)."""
        page = self._save_page("JS url cased page", JAVASCRIPT_URL_CASED)
        self._assert_save_and_render(page, LIVE_JS_URL)

    @skipUnless("mezzanine.pages" in settings.INSTALLED_APPS, "pages app required")
    def test_math_mxss_stripped_on_save_and_render(self):
        """mXSS ``<math>`` vectors do not survive save or render as live markup."""
        page = self._save_page("Math mutation page", MATH_MXSS)
        self._assert_save_and_render(page, LIVE_MATH + LIVE_ONERROR_ATTR)

    @skipUnless("mezzanine.pages" in settings.INSTALLED_APPS, "pages app required")
    def test_math_img_onerror_stripped_on_save_and_render(self):
        """Nested ``<math><img onerror>`` is neutralized on save and render."""
        page = self._save_page("Math img page", MATH_SIMPLE)
        self._assert_save_and_render(page, LIVE_MATH + LIVE_ONERROR_ATTR)

    @skipUnless("mezzanine.pages" in settings.INSTALLED_APPS, "pages app required")
    def test_thumbnails_filter_does_not_revive_math_mxss(self):
        """
        ``thumbnails()`` parses HTML when MEDIA_URL is present; a ``<math>``
        payload must stay dead after that rewrite under default filters.
        """
        payload = (
            '<p><img src="%sx.jpg" width="1" height="1"></p>%s'
            % (settings.MEDIA_URL, MATH_SIMPLE)
        )
        page = self._save_page("Thumbnails mutation page", payload)
        self._assert_save_and_render(
            page, LIVE_MATH + LIVE_ONERROR_ATTR + LIVE_SCRIPT, LIVE_SCRIPT_ALERT
        )

    @skipUnless("mezzanine.forms" in settings.INSTALLED_APPS, "forms app required")
    def test_form_upload_filename_img_xss(self):
        """
        CVE-2025-29573: a filename ``"><img…>`` must not break out of the
        entries table markup.
        """
        form = Form.objects.create(
            title="Filename XSS", status=CONTENT_STATUS_PUBLISHED
        )
        field = form.fields.create(
            label="File", field_type=fields.FILE, required=False, visible=True
        )
        entry = FormEntry.objects.create(form=form, entry_time=now())
        FieldEntry.objects.create(
            entry=entry, field_id=field.id, value="forms/abc/%s" % FILENAME_XSS
        )
        self.client.login(username=self._username, password=self._password)
        response = self.client.post(
            reverse("admin:form_entries", args=(form.id,)),
            {"field_%s_export" % field.id: "on", "field_0_export": "on"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, FILENAME_XSS)
        self.assertContains(response, html_escape(FILENAME_XSS))
        self._assert_absent(
            response.content.decode("utf-8"), LIVE_ONERROR_ATTR, "entries table"
        )

    @skipUnless("mezzanine.blog" in settings.INSTALLED_APPS, "blog app required")
    def test_title_in_json_not_served_as_html(self):
        """
        CVE-2025-6050: a script in a Displayable title is JSON data, not HTML.
        """
        self.client.login(username=self._username, password=self._password)
        BlogPost.objects.create(
            title=TITLE_XSS, user=self._user, status=CONTENT_STATUS_PUBLISHED
        )
        response = self.client.get(reverse("displayable_links_js"))
        self.assertEqual(response.status_code, 200)
        content_type = response["Content-Type"].split(";")[0]
        self.assertEqual(content_type, "application/json")
        self.assertNotIn("text/html", response["Content-Type"])
        body = response.content.decode("utf-8").lstrip()
        self.assertTrue(body.startswith("[") or body.startswith("{"))
        data = response.json()
        self.assertIsInstance(data, list)
        titles = [item.get("title", "") for item in data]
        self.assertTrue(
            any(TITLE_XSS in title for title in titles),
            "XSS title missing from JSON link list: %r" % titles,
        )

    def test_default_richtext_filters_bleach_after_thumbnails(self):
        """Last default filter is bleach; it runs after thumbnails (mXSS)."""
        filters = list(settings.RICHTEXT_FILTERS)
        self.assertEqual(filters[-1], "mezzanine.utils.html.escape")
        self.assertIn("mezzanine.utils.html.thumbnails", filters)
        self.assertLess(
            filters.index("mezzanine.utils.html.thumbnails"),
            filters.index("mezzanine.utils.html.escape"),
        )

    @skipUnless("mezzanine.pages" in settings.INSTALLED_APPS, "pages app required")
    def test_script_bypassing_form_clean_stripped_on_read(self):
        """
        ``Model.save()`` skips ``RichTextField.clean``; |richtext_filters
        must still bleach so ``<script>`` does not survive render.
        """
        page = RichTextPage.objects.create(
            title="Unclean save",
            content=SCRIPT,
            status=CONTENT_STATUS_PUBLISHED,
        )
        self.assertIn("<script>", page.content.lower())
        rendered = self._render_filters(page.content)
        self._assert_absent(rendered, LIVE_SCRIPT, "|richtext_filters")
        self._assert_dom_safe(rendered, "|richtext_filters")
        response = self.client.get(page.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self._assert_absent(
            response.content.decode("utf-8"), LIVE_SCRIPT_ALERT, "HTTP render"
        )

    def test_custom_filter_non_safetext_raises(self):
        """Custom filters that return non-SafeText raise TypeError."""
        original = settings.RICHTEXT_FILTERS
        settings.RICHTEXT_FILTERS = ("tests.test_sanitize.plain_string_filter",)
        try:
            with self.assertRaises(TypeError) as raised:
                self._render_filters("<p>ok</p>")
            self.assertIn("SafeText", str(raised.exception))
            self.assertIn("plain_string_filter", str(raised.exception))
        finally:
            settings.RICHTEXT_FILTERS = original

    def test_configured_none_without_env_still_bleaches(self):
        """RICHTEXT_FILTER_LEVEL=NONE is ignored unless the env hatch is set."""
        with mock.patch.dict(os.environ, {"NOVA_FORCE_RAW_HTML": "0"}):
            with override_settings(RICHTEXT_FILTER_LEVEL=RICHTEXT_FILTER_LEVEL_NONE):
                cleaned = richtext_escape(SCRIPT)
        self.assertNotIn("<script>", cleaned.lower())

    def test_nova_force_raw_html_escape_hatch(self):
        """NOVA_FORCE_RAW_HTML=1 is the only path that disables filtering."""
        with mock.patch.dict(os.environ, {"NOVA_FORCE_RAW_HTML": "1"}):
            raw = richtext_escape(SCRIPT)
        self.assertIn("<script>", raw.lower())

    def test_description_templates_stop_raw_safe(self):
        """Blog list and search results must not mark descriptions |safe."""
        root = Path(path_for_import("mezzanine"))
        blog_list = (root / "blog/templates/blog/blog_post_list.html").read_text()
        search = (root / "core/templates/search_results.html").read_text()
        self.assertNotIn("description_from_content|safe", blog_list)
        self.assertNotIn("|safe", search.split("result.description")[1].split("}}")[0])

    @skipUnless("mezzanine.pages" in settings.INSTALLED_APPS, "pages app required")
    def test_search_description_html_is_escaped(self):
        """User-supplied MetaData.description is not rendered as raw HTML."""
        RichTextPage.objects.create(
            title="Search desc xss",
            content="<p>visible body</p>",
            status=CONTENT_STATUS_PUBLISHED,
            description=FILENAME_XSS,
            gen_description=False,
        )
        response = self.client.get(reverse("search") + "?q=Search+desc+xss")
        self.assertEqual(response.status_code, 200)
        body = response.content.decode("utf-8")
        self.assertNotIn(FILENAME_XSS, body)
        self._assert_absent(body, LIVE_ONERROR_ATTR, "search description")
