"""PR-023a: SiteRole isolation and the narrow capability helper."""

import pytest
from django.contrib import admin
from django.contrib.sites.models import Site
from django.core.exceptions import PermissionDenied
from django.db import IntegrityError
from django.http import Http404
from django.utils.timezone import now

from mezzanine.core.capabilities import (
    CAP_PREVIEW_ISSUE,
    user_can_edit,
    user_can_issue_preview,
    user_has_capability,
)
from mezzanine.core.models import (
    CONTENT_STATUS_PUBLISHED,
    ROLE_AUTHOR,
    ROLE_EDITOR,
    SiteRole,
)
from mezzanine.core.views import set_site
from mezzanine.forms import fields
from mezzanine.forms.admin import FormAdmin
from mezzanine.forms.models import FieldEntry, Form, FormEntry
from mezzanine.pages.models import Page
from mezzanine.utils.sites import has_site_permission, override_current_site_id
from tests.factories import (
    AuthorFactory,
    BlogPostFactory,
    EditorFactory,
    PublisherFactory,
    RichTextPageFactory,
    SuperUserFactory,
    grant_site_permission,
)

pytestmark = pytest.mark.django_db


def test_siterole_unique_user_site(author_user):
    site_id = SiteRole.objects.get(user=author_user).site_id
    with pytest.raises(IntegrityError):
        SiteRole.objects.create(
            user=author_user, site_id=site_id, role=ROLE_EDITOR
        )


def test_author_factory_is_author_role(author_user):
    row = SiteRole.objects.get(user=author_user)
    assert row.role == ROLE_AUTHOR


def test_staff_a_cannot_get_site_b_page(author_user):
    site2 = Site.objects.create(domain="tenancy-b.example.com", name="Tenant B")
    local = RichTextPageFactory(title="Site A Page")
    with override_current_site_id(site2.pk):
        foreign = RichTextPageFactory(title="Site B Page", site=site2)

    assert Page.objects.get(pk=local.pk).pk == local.pk
    with pytest.raises(Page.DoesNotExist):
        Page.objects.get(pk=foreign.pk)


def test_staff_a_cannot_file_view_site_b_entry(author_user, rf):
    site2 = Site.objects.create(domain="tenancy-fv.example.com", name="FV B")
    with override_current_site_id(site2.pk):
        form = Form.objects.create(
            title="Other site form",
            site=site2,
            status=CONTENT_STATUS_PUBLISHED,
        )
        field = form.fields.create(
            label="File", field_type=fields.FILE, required=False, visible=True
        )
        entry = FormEntry.objects.create(form=form, entry_time=now())
        field_entry = FieldEntry.objects.create(
            entry=entry, field_id=field.id, value="forms/abc/secret.pdf"
        )
    request = rf.get("/")
    request.user = author_user
    with pytest.raises(Http404):
        FormAdmin(Form, admin.site).file_view(request, field_entry.id)


def test_has_site_permission_is_per_site(author_user):
    site2 = Site.objects.create(domain="tenancy-perm.example.com", name="Perm B")
    author_user.has_site_permission = True
    assert has_site_permission(author_user) is True
    author_user.has_site_permission = False
    assert has_site_permission(author_user) is False
    # Middleware would look up SiteRole; no row on site 2.
    assert not SiteRole.objects.filter(user=author_user, site=site2).exists()


def test_author_cannot_issue_preview(author_user):
    page = RichTextPageFactory(title="Author Cannot Preview")
    assert user_can_issue_preview(author_user, obj=page) is False
    assert user_has_capability(author_user, CAP_PREVIEW_ISSUE) is False


def test_publisher_can_issue_preview():
    publisher = PublisherFactory()
    page = RichTextPageFactory(title="Publisher Can Preview")
    assert user_can_issue_preview(publisher, obj=page) is True


def test_author_edits_own_blog_not_others():
    author = AuthorFactory()
    other = AuthorFactory()
    own = BlogPostFactory(title="Mine", user=author)
    theirs = BlogPostFactory(title="Theirs", user=other)
    assert user_can_edit(author, own) is True
    assert user_can_edit(author, theirs) is False


def test_editor_edits_any_blog_on_site():
    editor = EditorFactory()
    author = AuthorFactory()
    post = BlogPostFactory(title="Any", user=author)
    assert user_can_edit(editor, post) is True


def test_author_cannot_edit_page():
    """Pages are not Ownable; authors have no page.edit."""
    author = AuthorFactory()
    page = RichTextPageFactory(title="Not owned")
    assert user_can_edit(author, page) is False
    assert user_can_edit(EditorFactory(), page) is True


def test_superuser_bypasses_siterole():
    admin_user = SuperUserFactory()
    page = RichTextPageFactory(title="Superuser page")
    assert user_can_issue_preview(admin_user, obj=page) is True
    assert user_can_edit(admin_user, page) is True
    assert not SiteRole.objects.filter(user=admin_user).exists()


def test_set_site_requires_post(author_user, rf):
    request = rf.get("/set_site/", {"site_id": 1})
    request.user = author_user
    request.session = {}
    response = set_site(request)
    assert response.status_code == 405


def test_set_site_denied_without_role_on_target(author_user, rf):
    site2 = Site.objects.create(domain="tenancy-switch.example.com", name="Switch")
    request = rf.post("/set_site/", {"site_id": site2.pk})
    request.user = author_user
    request.session = {}
    with pytest.raises(PermissionDenied):
        set_site(request)


def test_set_site_allowed_with_role_on_target(author_user, rf):
    site2 = Site.objects.create(domain="tenancy-ok.example.com", name="OK")
    grant_site_permission(author_user, site_id=site2.pk, role=ROLE_AUTHOR)
    request = rf.post("/set_site/", {"site_id": site2.pk})
    request.user = author_user
    request.session = {}
    response = set_site(request)
    assert response.status_code == 302
    assert request.session["site_id"] == site2.pk


def test_author_view_draft_is_forbidden(author_user, rf):
    page = RichTextPageFactory(title="No Token For Author")
    from mezzanine.pages.admin import PageAdmin
    from mezzanine.pages.models import RichTextPage

    request = rf.get("/")
    request.user = author_user
    with pytest.raises(PermissionDenied):
        PageAdmin(RichTextPage, admin.site).view_draft_view(request, page.pk)
