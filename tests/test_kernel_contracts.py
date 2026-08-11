"""Characterization suite. Flip comments mark Wave 3 PRs.

Locks *current* kernel behaviour (design 2.4) before 020–022c cut over.
Do not "fix" staff-sees-drafts here — later PRs flip the assertions
in this file. 020 nestable ``override_current_site_id`` is done.
"""

import os
from contextlib import contextmanager

import pytest
from django.apps import apps
from django.contrib import admin
from django.contrib.auth.models import AnonymousUser
from django.contrib.redirects.models import Redirect
from django.contrib.sites.models import Site
from django.db.models import UniqueConstraint
from django.http import Http404, HttpResponse
from django.template import Context, Template
from django.test import RequestFactory, override_settings
from django.utils.deprecation import MiddlewareMixin
from django.utils.timezone import now

from mezzanine.conf import settings
from mezzanine.core.models import (
    CONTENT_STATUS_DRAFT,
    CONTENT_STATUS_PUBLISHED,
    Displayable,
)
from mezzanine.core.templatetags.mezzanine_tags import richtext_filters
from mezzanine.forms import fields
from mezzanine.forms.admin import FormAdmin
from mezzanine.forms.models import FieldEntry, Form, FormEntry
from mezzanine.pages.middleware import PageMiddleware
from mezzanine.pages.models import Link, Page, RichTextPage
from mezzanine.pages.page_processors import processor_for, processors
from mezzanine.pages.views import page as page_view
from mezzanine.utils.sites import current_site_id, override_current_site_id
from tests.factories import (
    AuthorFactory,
    BlogPostFactory,
    PageFactory,
    RichTextPageFactory,
)

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def _clear_site_override():
    """020 done: reset nestable override stack so tests do not leak."""
    from mezzanine.utils.sites import _site_id_override_stack

    token = _site_id_override_stack.set(())
    yield
    _site_id_override_stack.reset(token)


@pytest.fixture
def rf():
    return RequestFactory()


@contextmanager
def _thread_request(request):
    from mezzanine.core.request import _current_request

    token = _current_request.set(request)
    try:
        yield request
    finally:
        _current_request.reset(token)


@contextmanager
def _restore_processors():
    snapshot = {key: list(value) for key, value in processors.items()}
    try:
        yield
    finally:
        processors.clear()
        processors.update(snapshot)


# ---------------------------------------------------------------------------
# 1. Displayable.get_absolute_url
# ---------------------------------------------------------------------------


def test_displayable_get_absolute_url_raises_on_base():
    """Abstract Displayable.get_absolute_url raises NotImplementedError.

    Displayable cannot be instantiated (abstract). Page / BlogPost override
    this. Call the mixin implementation on an unsaved dummy that does not
    define get_absolute_url.
    """
    dummy = type("DummyDisplayable", (), {})()
    with pytest.raises(NotImplementedError, match="get_absolute_url"):
        Displayable.get_absolute_url(dummy)


# ---------------------------------------------------------------------------
# 2. Page.get_slug / set_slug / set_parent
# ---------------------------------------------------------------------------


def test_page_get_slug_is_parent_prefixed():
    parent = RichTextPageFactory(title="About Us")
    child = RichTextPage(title="The Team", parent=parent)
    assert child.get_slug() == f"{parent.slug}/the-team"


def test_page_set_slug_rewrites_descendants():
    parent = RichTextPageFactory(title="Parent")
    child = RichTextPageFactory(title="Child", parent=parent)
    assert child.slug.startswith(f"{parent.slug}/")
    parent.set_slug("renamed-parent")
    child.refresh_from_db()
    assert parent.slug == "renamed-parent"
    assert child.slug == "renamed-parent/child"


def test_page_set_parent_raises_attribute_error_on_cycle():
    parent = RichTextPageFactory(title="Cycle Parent")
    child = RichTextPageFactory(title="Cycle Child")
    child.set_parent(parent)
    with pytest.raises(AttributeError, match="parent"):
        parent.set_parent(parent)
    with pytest.raises(AttributeError, match="parent"):
        parent.set_parent(child)


def test_link_http_slug_not_rewritten_on_set_parent():
    """Link slugs starting with http are NOT suffix-rewritten on set_parent."""
    parent = RichTextPageFactory(title="Nav")
    https_link = Link.objects.create(
        title="HTTPS", slug="https://example.com/out"
    )
    http_link = Link.objects.create(
        title="HTTP", slug="http://example.com/out"
    )
    https_link.set_parent(parent)
    http_link.set_parent(parent)
    https_link.refresh_from_db()
    http_link.refresh_from_db()
    assert https_link.slug == "https://example.com/out"
    assert http_link.slug == "http://example.com/out"


def test_non_http_link_slug_is_rewritten_on_set_parent():
    parent = RichTextPageFactory(title="Nav Internal")
    link = Link.objects.create(title="Internal", slug="internal-link")
    link.set_parent(parent)
    link.refresh_from_db()
    assert link.slug == f"{parent.slug}/internal-link"


# ---------------------------------------------------------------------------
# 3. Slug uniqueness (UniqueConstraint(site, slug) — 021 done)
# ---------------------------------------------------------------------------


def test_auto_slugs_unique_per_concrete_slugged_type():
    """unique_slug on save: two Pages on the same site cannot share an
    auto-generated slug. 021 done: UniqueConstraint(site, slug) on pages.Page.
    """
    first = RichTextPageFactory(title="Shared Auto Title")
    second = RichTextPageFactory(title="Shared Auto Title")
    assert first.slug == "shared-auto-title"
    assert second.slug == "shared-auto-title-1"
    assert first.slug != second.slug


def test_page_and_richtextpage_share_page_slug_namespace():
    """All Page MTI children share the Page (base_concrete_model(Slugged)) ns.

    021 done: UniqueConstraint lives on pages_page, not pages_richtextpage.
    """
    bare = PageFactory(title="Mti Namespace")
    typed = RichTextPageFactory(title="Mti Namespace")
    assert bare.slug != typed.slug


def test_blogpost_slug_namespace_is_separate_from_page():
    """BlogPost slugs are a separate unique_slug namespace from Page.

    021 done: UniqueConstraint(site, slug) on blog.BlogPost independently.
    """
    page = RichTextPageFactory(title="Cross App Slug")
    post = BlogPostFactory(title="Cross App Slug")
    assert page.slug == post.slug == "cross-app-slug"


def test_unique_constraint_on_page_and_blogpost_site_slug():
    """021 done: UniqueConstraint(fields=['site', 'slug'])."""
    for model in (Page, apps.get_model("blog", "BlogPost")):
        slug_constraints = [
            c
            for c in model._meta.constraints
            if isinstance(c, UniqueConstraint) and "slug" in c.fields
        ]
        assert len(slug_constraints) == 1
        constraint = slug_constraints[0]
        assert list(constraint.fields) == ["site", "slug"]
        assert constraint.name == f"{model._meta.model_name}_site_slug"


def test_explicit_duplicate_page_slugs_raise_integrity_error():
    """021 done: second save raises IntegrityError under UniqueConstraint(site, slug).

    unique_slug only runs when slug is blank. Explicit dupes used to persist.
    """
    from django.db import IntegrityError, transaction

    RichTextPageFactory(title="Explicit A", slug="manual-dup")
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            RichTextPageFactory(title="Explicit B", slug="manual-dup")


def test_explicit_duplicate_blogpost_slugs_raise_integrity_error():
    """021 done: UniqueConstraint(site, slug) on blog.BlogPost independently."""
    from django.db import IntegrityError, transaction

    BlogPostFactory(title="Explicit A", slug="manual-dup-post")
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            BlogPostFactory(title="Explicit B", slug="manual-dup-post")


def test_same_slug_allowed_across_sites():
    """UniqueConstraint is per (site, slug), not global."""
    site2 = Site.objects.create(domain="slug-site2.example.com", name="Slug 2")
    page = RichTextPageFactory(title="Cross Site", slug="cross-site-slug")
    with override_current_site_id(site2.pk):
        other = RichTextPageFactory(
            title="Cross Site", slug="cross-site-slug", site=site2
        )
    assert page.slug == other.slug == "cross-site-slug"
    assert page.site_id != other.site_id


def test_nova_dedupe_slugs_dry_run_on_unique_slugs():
    """021 done: command is registered; unique rows are a no-op."""
    from io import StringIO

    from django.core.management import call_command

    RichTextPageFactory(title="Unique A", slug="unique-a-cmd")
    BlogPostFactory(title="Unique Post", slug="unique-post-cmd")
    out = StringIO()
    call_command("nova_dedupe_slugs", "--dry-run", stdout=out)
    text = out.getvalue()
    assert "no (site, slug) collisions" in text
    assert "dry-run: no slugs rewritten" in text


def test_rewrite_page_slug_updates_children_like_set_slug():
    """021 done: dedupe child rewrite follows Page.set_slug prefix rules."""
    from mezzanine.core.management.commands.nova_dedupe_slugs import (
        is_http_link,
        rewrite_page_slug,
    )

    parent = RichTextPageFactory(title="P", slug="rewrite-parent")
    child = RichTextPageFactory(
        title="C", slug="rewrite-parent/kid", parent=parent
    )
    http_link = Link.objects.create(
        title="Out", slug="https://example.com/rewrite", parent=parent
    )
    assert is_http_link(http_link)
    rewrite_page_slug(parent, "rewrite-parent-99")
    parent.refresh_from_db()
    child.refresh_from_db()
    http_link.refresh_from_db()
    assert parent.slug == "rewrite-parent-99"
    assert child.slug == "rewrite-parent-99/kid"
    assert http_link.slug == "https://example.com/rewrite"


# ---------------------------------------------------------------------------
# 4. processor_for — merge dicts / short-circuit on HttpResponse
# ---------------------------------------------------------------------------


def test_processor_for_model_and_slug_still_register():
    """processor_for(Model) and processor_for("some/slug") still register.

    Existing coverage: tests/test_pages.py
    test_unicode_slug_parm_to_processor_for, test_exact_page_processor_for.
    """
    with _restore_processors():

        @processor_for(RichTextPage)
        def _model_proc(request, page):
            return {"from_model": True}

        @processor_for("some/slug")
        def _slug_proc(request, page):
            return {"from_slug": True}

        model_fns = [fn for fn, _exact in processors["richtextpage"]]
        slug_fns = [fn for fn, _exact in processors["slug:some/slug"]]
        assert _model_proc in model_fns
        assert _slug_proc in slug_fns


def test_processor_returning_httpresponse_short_circuits(rf):
    """A processor that returns HttpResponse short-circuits page rendering."""
    page = RichTextPageFactory(title="Short Circuit Page")
    with _restore_processors():

        @processor_for(page.slug)
        def _short(request, current):
            return HttpResponse("kernel-short-circuit")

        request = rf.get(page.get_absolute_url())
        request.user = AnonymousUser()
        response = PageMiddleware(lambda req: None).process_view(
            request, page_view, [], {}
        )
    assert isinstance(response, HttpResponse)
    assert response.content == b"kernel-short-circuit"


def test_processor_for_model_httpresponse_short_circuits(rf):
    page = RichTextPageFactory(title="Model Short Circuit")
    with _restore_processors():

        @processor_for(RichTextPage)
        def _short(request, current):
            return HttpResponse("model-short-circuit")

        request = rf.get(page.get_absolute_url())
        request.user = AnonymousUser()
        response = PageMiddleware(lambda req: None).process_view(
            request, page_view, [], {}
        )
    assert isinstance(response, HttpResponse)
    assert response.content == b"model-short-circuit"


def test_processors_merge_dicts_first_key_wins(rf):
    """Slug processors run before model processors; existing keys are kept."""
    page = RichTextPageFactory(title="Merge Dicts Page")
    with _restore_processors():

        @processor_for(page.slug)
        def _slug_proc(request, current):
            return {"from_slug": True, "shared": "slug"}

        @processor_for(RichTextPage)
        def _model_proc(request, current):
            return {"from_model": True, "shared": "model"}

        request = rf.get(page.get_absolute_url())
        request.user = AnonymousUser()
        response = PageMiddleware(lambda req: None).process_view(
            request, page_view, [], {}
        )
    assert response.context_data["from_slug"] is True
    assert response.context_data["from_model"] is True
    assert response.context_data["shared"] == "slug"


# ---------------------------------------------------------------------------
# 5. PageMiddleware attaches the deepest prefix page
# ---------------------------------------------------------------------------


def test_page_middleware_attaches_deepest_prefix(rf):
    about = RichTextPageFactory(title="About Prefix")
    team = RichTextPageFactory(title="Team Prefix", parent=about)
    request = rf.get(f"/{team.slug}/mike/")
    request.user = AnonymousUser()

    def _app_view(request, *args, **kwargs):
        return HttpResponse("app")

    PageMiddleware(lambda req: None).process_view(request, _app_view, [], {})
    assert request.page.pk == team.pk


def test_page_middleware_blog_post_uses_blog_listing_page(rf):
    """Blog post URL still has request.page = blog listing page if it exists."""
    blog_page = RichTextPageFactory(title="Blog", slug=settings.BLOG_SLUG)
    post = BlogPostFactory()
    request = rf.get(post.get_absolute_url())
    request.user = AnonymousUser()

    def _app_view(request, *args, **kwargs):
        return HttpResponse("post")

    PageMiddleware(lambda req: None).process_view(request, _app_view, [], {})
    assert request.page.pk == blog_page.pk


# ---------------------------------------------------------------------------
# 6. published() split + PreviewToken (022b)
# ---------------------------------------------------------------------------


def test_displayable_published_instance_ignores_staff():
    """Instance method does NOT look at is_staff.

    022a: document this. 022c: staff GET without token → 404 (view/manager),
    instance method stays date/status-only.
    """
    draft = RichTextPageFactory(title="Draft Instance", status=CONTENT_STATUS_DRAFT)
    AuthorFactory()  # staff exists; instance method still ignores them
    assert draft.published() is False


def test_published_manager_staff_short_circuits_to_all():
    """PublishedManager.published(for_user=staff) returns self.all().

    022c: stop short-circuiting on is_staff; staff drafts need a token.
    """
    draft = RichTextPageFactory(title="Draft Manager", status=CONTENT_STATUS_DRAFT)
    staff = AuthorFactory()
    anon = AnonymousUser()
    def pks(qs):
        return set(qs.values_list("pk", flat=True))

    assert draft.pk not in pks(Page.objects.published())
    assert draft.pk not in pks(Page.objects.published(for_user=anon))
    assert draft.pk in pks(Page.objects.published(for_user=staff))


def test_staff_get_draft_is_200_without_token(author_user, rf):
    """Staff published() bypass attaches the draft; page view would be 200.

    Full template render is skipped (Django 6.1 widget ``__proxy__`` on
    ``{% editable %}``). 022c: staff GET without token → 404.
    """
    draft = RichTextPageFactory(
        title="Staff Visible Draft", status=CONTENT_STATUS_DRAFT
    )
    request = rf.get(draft.get_absolute_url())
    request.user = author_user
    response = PageMiddleware(lambda req: None).process_view(
        request, page_view, [], {}
    )
    assert request.page.pk == draft.pk
    assert response is not None
    assert response.status_code == 200


def test_anon_get_draft_is_404(rf):
    draft = RichTextPageFactory(title="Anon Hidden Draft", status=CONTENT_STATUS_DRAFT)
    request = rf.get(draft.get_absolute_url())
    request.user = AnonymousUser()
    response = PageMiddleware(lambda req: None).process_view(
        request, page_view, [], {}
    )
    assert getattr(request, "page", None) is None
    assert response is None


def test_preview_token_model_exists():
    """022b: PreviewToken is a hashed DB capability, not a signed blob."""
    PreviewToken = apps.get_model("core", "PreviewToken")
    assert PreviewToken._meta.get_field("token_hash").max_length == 64
    assert PreviewToken._meta.get_field("token_hash").unique
    assert PreviewToken._meta.get_field("as_role").max_length == 8


# ---------------------------------------------------------------------------
# 7. Two-site isolation (CurrentSiteManager + file_view Wave 0 fix)
# ---------------------------------------------------------------------------


def test_page_objects_filtered_to_current_site():
    """SiteRelated managers filter by current_site_id().

    023a: SiteRole isolation tests live in tests/test_tenancy.py; this
    file keeps the CurrentSiteManager contract.
    """
    site2 = Site.objects.create(domain="iso-site2.example.com", name="Iso 2")
    local = RichTextPageFactory(title="Site One Page")
    with override_current_site_id(site2.pk):
        foreign = RichTextPageFactory(title="Site Two Page", site=site2)

    assert Page.objects.get(pk=local.pk).pk == local.pk
    with pytest.raises(Page.DoesNotExist):
        Page.objects.get(pk=foreign.pk)

    # Unfiltered base manager still sees the other site's row.
    assert Page._base_manager.get(pk=foreign.pk).pk == foreign.pk

    with override_current_site_id(site2.pk):
        assert Page.objects.get(pk=foreign.pk).pk == foreign.pk
        with pytest.raises(Page.DoesNotExist):
            Page.objects.get(pk=local.pk)


def test_staff_get_other_site_draft_404s_when_site_id_is_theirs(author_user, rf):
    """Staff on site 1 cannot resolve a site-2 draft (manager is site-scoped).

    Staff-sees-drafts does not pierce CurrentSiteManager. 022c: same-site
    draft GET without token also 404s. 023a: per-(user, site) SiteRole.
    """
    site2 = Site.objects.create(domain="draft-site2.example.com", name="Draft 2")
    with override_current_site_id(site2.pk):
        foreign_draft = RichTextPageFactory(
            title="Foreign Draft",
            slug="foreign-draft-only",
            site=site2,
            status=CONTENT_STATUS_DRAFT,
        )
    request = rf.get(foreign_draft.get_absolute_url())
    request.user = author_user
    response = PageMiddleware(lambda req: None).process_view(
        request, page_view, [], {}
    )
    assert getattr(request, "page", None) is None
    assert response is None


def test_file_view_cross_site_404(author_user, rf):
    """file_view was fixed in Wave 0: FieldEntry is joined to current_site_id."""
    site2 = Site.objects.create(domain="fv-site2.example.com", name="FV 2")
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


# ---------------------------------------------------------------------------
# 8. current_site_id resolution + nested override (020 done)
# ---------------------------------------------------------------------------


def test_current_site_id_falls_back_to_settings_site_id():
    """Last resort is SITE_ID when override / request / env are absent."""
    from mezzanine.core.request import _current_request

    old = os.environ.pop("MEZZANINE_SITE_ID", None)
    token = _current_request.set(None)
    try:
        assert current_site_id() == settings.SITE_ID
    finally:
        if old is not None:
            os.environ["MEZZANINE_SITE_ID"] = old
        _current_request.reset(token)


def test_current_site_id_mezzanine_env_beats_settings(monkeypatch):
    from mezzanine.core.request import _current_request

    site2 = Site.objects.create(domain="env-site.example.com", name="Env")
    monkeypatch.setenv("MEZZANINE_SITE_ID", str(site2.pk))
    token = _current_request.set(None)
    try:
        assert int(current_site_id()) == site2.pk
    finally:
        _current_request.reset(token)


@override_settings(ALLOWED_HOSTS=["*"])
def test_current_site_id_host_beats_env(rf, monkeypatch):
    site_host = Site.objects.create(domain="host-wins.example.com", name="Host")
    site_env = Site.objects.create(domain="env-loses.example.com", name="Env")
    monkeypatch.setenv("MEZZANINE_SITE_ID", str(site_env.pk))
    request = rf.get("/")
    request.META["HTTP_HOST"] = "host-wins.example.com"
    request.session = {}
    with _thread_request(request):
        assert current_site_id() == site_host.pk


@override_settings(ALLOWED_HOSTS=["*"])
def test_current_site_id_session_beats_host(rf):
    site_session = Site.objects.create(domain="sess.example.com", name="Sess")
    Site.objects.create(domain="host-loses.example.com", name="Host loses")
    request = rf.get("/")
    request.META["HTTP_HOST"] = "host-loses.example.com"
    request.session = {"site_id": site_session.pk}
    with _thread_request(request):
        assert current_site_id() == site_session.pk


def test_current_site_id_request_attr_beats_session(rf):
    site_attr = Site.objects.create(domain="attr.example.com", name="Attr")
    site_session = Site.objects.create(domain="sess2.example.com", name="Sess2")
    request = rf.get("/")
    request.site_id = site_attr.pk
    request.session = {"site_id": site_session.pk}
    with _thread_request(request):
        assert current_site_id() == site_attr.pk


def test_current_site_id_override_beats_request_attr(rf):
    site_override = Site.objects.create(domain="ovr.example.com", name="Ovr")
    site_attr = Site.objects.create(domain="attr2.example.com", name="Attr2")
    request = rf.get("/")
    request.site_id = site_attr.pk
    request.session = {}
    with _thread_request(request):
        with override_current_site_id(site_override.pk):
            assert current_site_id() == site_override.pk
        assert current_site_id() == site_attr.pk


def test_nested_override_current_site_id_raises_recursion_error():
    """020 done: nestable override (no RecursionError)."""
    assert current_site_id() == settings.SITE_ID
    with override_current_site_id(2):
        assert current_site_id() == 2
        with override_current_site_id(3):
            assert current_site_id() == 3
        assert current_site_id() == 2
    assert current_site_id() == settings.SITE_ID


def test_current_request_survives_inner_process_response(rf):
    """Reset only after CurrentRequestMiddleware.process_response (last)."""
    from mezzanine.core.request import CurrentRequestMiddleware, current_request

    seen = {}

    class InnerMiddleware(MiddlewareMixin):
        def process_response(self, request, response):
            seen["inner_request"] = current_request()
            seen["inner_site"] = current_site_id()
            return response

    def view(request):
        seen["view_request"] = current_request()
        seen["view_site"] = current_site_id()
        return HttpResponse("ok")

    site2 = Site.objects.create(domain="inner.example.com", name="Inner")
    request = rf.get("/")
    request.site_id = site2.pk
    request.session = {}

    inner = InnerMiddleware(view)
    outer = CurrentRequestMiddleware(inner)
    response = outer(request)

    assert response.status_code == 200
    assert seen["view_request"] is request
    assert seen["view_site"] == site2.pk
    assert seen["inner_request"] is request
    assert seen["inner_site"] == site2.pk
    assert current_request() is None


def test_redirect_fallback_on_404_uses_request_site(rf):
    """404 process_response still resolves Redirect against the request site."""
    from mezzanine.core.middleware import RedirectFallbackMiddleware
    from mezzanine.core.request import CurrentRequestMiddleware, current_request

    site2 = Site.objects.create(domain="redir.example.com", name="Redir")
    Redirect.objects.create(site_id=site2.pk, old_path="/gone/", new_path="/here/")

    def view(request):
        return HttpResponse("missing", status=404)

    request = rf.get("/gone/")
    request.site_id = site2.pk
    request.session = {}

    inner = RedirectFallbackMiddleware(view)
    outer = CurrentRequestMiddleware(inner)
    response = outer(request)

    assert response.status_code == 301
    assert response["Location"] == "/here/"
    assert current_request() is None


# ---------------------------------------------------------------------------
# 9. |richtext_filters default pipeline strips <script>
# ---------------------------------------------------------------------------


def test_richtext_filters_default_pipeline_strips_script():
    """Thin pointer; tests/test_sanitize.py covers the pipeline in depth."""
    rendered = richtext_filters("<p>ok</p><script>alert(1)</script>")
    text = str(rendered)
    assert "<script>" not in text.lower()
    assert "ok" in text

    via_template = Template(
        "{% load mezzanine_tags %}{{ html|richtext_filters }}"
    ).render(Context({"html": "<p>ok</p><script>alert(1)</script>"}))
    assert "<script>" not in via_template.lower()


# ---------------------------------------------------------------------------
# 10. url_map
# ---------------------------------------------------------------------------


def test_url_map_anon_excludes_drafts():
    """022c: url_map excludes drafts without a token for every for_user."""
    draft = RichTextPageFactory(title="Urlmap Draft", status=CONTENT_STATUS_DRAFT)
    published = RichTextPageFactory(
        title="Urlmap Published", status=CONTENT_STATUS_PUBLISHED
    )
    mapping = Displayable.objects.url_map(for_user=AnonymousUser())
    assert published.get_absolute_url() in mapping
    assert draft.get_absolute_url() not in mapping


def test_url_map_staff_currently_includes_drafts():
    """url_map(for_user=staff) includes drafts because published() short-circuits.

    022c: staff map excludes drafts unless a preview token covers them.
    """
    draft = RichTextPageFactory(
        title="Urlmap Staff Draft", status=CONTENT_STATUS_DRAFT
    )
    staff = AuthorFactory()
    mapping = Displayable.objects.url_map(for_user=staff)
    assert draft.get_absolute_url() in mapping
