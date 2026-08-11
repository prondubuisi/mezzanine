"""Preview tokens and the 022c staff-bypass cutover.

A draft is 404 without a token, including for staff.
"""

from datetime import timedelta

import pytest
from django.contrib.auth.models import AnonymousUser
from django.contrib.sites.models import Site
from django.core.cache import cache
from django.http import Http404, HttpResponse
from django.test import RequestFactory, override_settings
from django.urls import re_path, reverse
from django.utils.timezone import now

from mezzanine.conf import settings
from mezzanine.core.middleware import PreviewTokenMiddleware
from mezzanine.core.models import (
    CONTENT_STATUS_DRAFT,
    CONTENT_STATUS_PUBLISHED,
    PREVIEW_ROLE_STAFF,
    PreviewToken,
)
from mezzanine.pages.models import Page
from mezzanine.pages.middleware import PageMiddleware
from mezzanine.pages.views import page as page_view
from mezzanine.utils.cache import cache_get, cache_installed, cache_key_prefix
from mezzanine.utils.deprecation import (
    get_middleware_setting,
    get_middleware_setting_name,
)
from tests.factories import BlogPostFactory, RichTextPageFactory, SuperUserFactory

pytestmark = pytest.mark.django_db


def _preview_cache_view(request):
    label = "preview-hit" if getattr(request, "preview", None) else "no-preview"
    return HttpResponse(label, content_type="text/html")


urlpatterns = [
    re_path(r"^preview-cache/$", _preview_cache_view),
]


def _middleware():
    return PreviewTokenMiddleware(lambda request: HttpResponse("ok"))


def test_preview_middleware_after_auth_before_page():
    mw = list(settings.MIDDLEWARE)
    preview = "mezzanine.core.middleware.PreviewTokenMiddleware"
    auth = "django.contrib.auth.middleware.AuthenticationMiddleware"
    page = "mezzanine.pages.middleware.PageMiddleware"
    assert preview in mw
    assert mw.index(auth) < mw.index(preview)
    assert mw.index(preview) < mw.index(page)


def test_issue_stores_hash_returns_raw_once(author_user):
    page = RichTextPageFactory(title="Issue Target")
    raw = PreviewToken.issue(page, created_by=author_user)
    assert raw
    assert not PreviewToken.objects.filter(token_hash=raw).exists()
    token = PreviewToken.objects.get()
    assert token.token_hash == PreviewToken.hash_token(raw)
    assert len(token.token_hash) == 64
    assert token.object_pk == str(page.pk)
    assert token.covers(Page)
    assert token.as_role == "anon"


def test_valid_token_sets_request_preview(author_user, rf):
    page = RichTextPageFactory(title="Preview Valid")
    raw = PreviewToken.issue(page, created_by=author_user)
    request = rf.get("/?preview=%s" % raw)
    request.user = AnonymousUser()
    assert _middleware().process_request(request) is None
    assert getattr(request, "preview", None) is not None
    assert request.preview.pk == PreviewToken.objects.get().pk
    PreviewToken.objects.get().refresh_from_db()
    assert PreviewToken.objects.get().last_seen_at is not None


def test_unknown_token_leaves_preview_unset(rf):
    request = rf.get("/?preview=not-a-real-token")
    request.user = AnonymousUser()
    assert _middleware().process_request(request) is None
    assert getattr(request, "preview", None) is None


def test_expired_token_leaves_preview_unset(author_user, rf):
    page = RichTextPageFactory(title="Preview Expired")
    raw = PreviewToken.issue(
        page, created_by=author_user, expires_at=now() - timedelta(minutes=1)
    )
    request = rf.get("/?preview=%s" % raw)
    request.user = AnonymousUser()
    assert _middleware().process_request(request) is None
    assert getattr(request, "preview", None) is None


def test_wrong_site_leaves_preview_unset(author_user, rf):
    page = RichTextPageFactory(title="Preview Other Site")
    raw = PreviewToken.issue(page, created_by=author_user)
    other = Site.objects.create(domain="other-preview.example.com", name="Other")
    PreviewToken.objects.update(site=other)
    request = rf.get("/?preview=%s" % raw)
    request.user = AnonymousUser()
    assert _middleware().process_request(request) is None
    assert getattr(request, "preview", None) is None


def test_staff_role_requires_authenticated_staff(author_user, rf):
    page = RichTextPageFactory(title="Preview Staff Role")
    raw = PreviewToken.issue(
        page, created_by=author_user, as_role=PREVIEW_ROLE_STAFF
    )
    anon_request = rf.get("/?preview=%s" % raw)
    anon_request.user = AnonymousUser()
    assert _middleware().process_request(anon_request) is None
    assert getattr(anon_request, "preview", None) is None

    staff_request = rf.get("/?preview=%s" % raw)
    staff_request.user = author_user
    assert _middleware().process_request(staff_request) is None
    assert getattr(staff_request, "preview", None) is not None


def test_preview_response_is_private_no_store(author_user, rf):
    page = RichTextPageFactory(title="Preview Headers")
    raw = PreviewToken.issue(page, created_by=author_user)
    request = rf.get("/?preview=%s" % raw)
    request.user = AnonymousUser()
    mw = _middleware()
    mw.process_request(request)
    response = mw.process_response(
        request, HttpResponse("ok", content_type="text/html")
    )
    cc = response["Cache-Control"]
    assert "private" in cc
    assert "no-store" in cc


def test_staff_draft_without_token_does_not_attach_page(author_user, rf):
    """022c: staff no longer sees drafts by URL. Middleware leaves page unset."""
    draft = RichTextPageFactory(
        title="Staff Hidden Without Token", status=CONTENT_STATUS_DRAFT
    )
    request = rf.get(draft.get_absolute_url())
    request.user = author_user
    response = PageMiddleware(lambda req: None).process_view(
        request, page_view, [], {}
    )
    assert getattr(request, "preview", None) is None
    assert getattr(request, "page", None) is None
    assert response is None


def test_draft_with_token_attaches_page(author_user, rf):
    draft = RichTextPageFactory(
        title="Previewed Draft", status=CONTENT_STATUS_DRAFT
    )
    raw = PreviewToken.issue(draft, created_by=author_user)
    request = rf.get(draft.get_absolute_url() + "?preview=" + raw)
    request.user = AnonymousUser()
    assert _middleware().process_request(request) is None
    response = PageMiddleware(lambda req: None).process_view(
        request, page_view, [], {}
    )
    assert request.preview is not None
    assert request.page.pk == draft.pk
    assert response is not None
    assert response.status_code == 200


def test_draft_parent_still_resolves_previewed_child(author_user, rf):
    """Previewing /about/team/ works when /about/ is also a draft."""
    parent = RichTextPageFactory(
        title="About Draft", slug="about-preview-chain", status=CONTENT_STATUS_DRAFT
    )
    child = RichTextPageFactory(
        title="Team Draft",
        slug="about-preview-chain/team",
        parent=parent,
        status=CONTENT_STATUS_DRAFT,
    )
    raw = PreviewToken.issue(child, created_by=author_user)
    request = rf.get(child.get_absolute_url() + "?preview=" + raw)
    request.user = AnonymousUser()
    assert _middleware().process_request(request) is None
    response = PageMiddleware(lambda req: None).process_view(
        request, page_view, [], {}
    )
    assert request.page.pk == child.pk
    assert response is not None
    assert response.status_code == 200
    ascendants = request.page.get_ascendants()
    assert [p.pk for p in ascendants] == [parent.pk]


def test_parent_token_does_not_reveal_draft_child(author_user, rf):
    parent = RichTextPageFactory(
        title="About Only", slug="about-token-parent", status=CONTENT_STATUS_DRAFT
    )
    child = RichTextPageFactory(
        title="Hidden Team",
        slug="about-token-parent/team",
        parent=parent,
        status=CONTENT_STATUS_DRAFT,
    )
    raw = PreviewToken.issue(parent, created_by=author_user)
    request = rf.get(child.get_absolute_url() + "?preview=" + raw)
    request.user = AnonymousUser()
    assert _middleware().process_request(request) is None
    with pytest.raises(Http404):
        PageMiddleware(lambda req: None).process_view(request, page_view, [], {})
    assert getattr(request, "page", None) is None or request.page.pk != child.pk


def test_page_menu_excludes_drafts_for_staff(author_user, rf):
    from django.template import Context, Template

    published = RichTextPageFactory(
        title="Published Menu Page", status=CONTENT_STATUS_PUBLISHED
    )
    draft = RichTextPageFactory(
        title="Draft Menu Page", status=CONTENT_STATUS_DRAFT
    )
    request = rf.get("/")
    request.user = author_user
    rendered = Template(
        "{% load pages_tags %}{% page_menu 'pages/menus/tree.html' %}"
    ).render(Context({"request": request}))
    assert published.title in rendered
    assert draft.title not in rendered


def test_blog_draft_requires_token(author_user, rf):
    """Blog drafts stay out of published(); a covering token unions the pk."""
    from mezzanine.blog.models import BlogPost
    from mezzanine.blog.views import blog_post_detail

    post = BlogPostFactory(title="Draft Post", status=CONTENT_STATUS_DRAFT)
    assert post.pk not in BlogPost.objects.published(
        for_user=author_user
    ).values_list("pk", flat=True)

    request = rf.get(post.get_absolute_url())
    request.user = author_user
    with pytest.raises(Http404):
        blog_post_detail(request, slug=post.slug)

    raw = PreviewToken.issue(post, created_by=author_user)
    token = PreviewToken.lookup(raw)
    assert post.pk in BlogPost.objects.published(preview=token).values_list(
        "pk", flat=True
    )
    request = rf.get(post.get_absolute_url() + "?preview=" + raw)
    request.user = AnonymousUser()
    assert _middleware().process_request(request) is None
    response = blog_post_detail(request, slug=post.slug)
    assert response.status_code == 200


def test_admin_view_draft_issues_token_and_redirects(client):
    user = SuperUserFactory()
    client.force_login(user)
    page = RichTextPageFactory(title="Admin View Draft", status=CONTENT_STATUS_DRAFT)
    url = reverse("admin:pages_richtextpage_view_draft", args=[page.pk])
    response = client.get(url)
    assert response.status_code == 302
    location = response["Location"]
    assert "preview=" in location
    raw = location.split("preview=", 1)[1]
    token = PreviewToken.lookup(raw)
    assert token is not None
    assert token.object_pk == str(page.pk)
    assert not PreviewToken.objects.filter(token_hash=raw).exists()


@override_settings(
    **{
        "ROOT_URLCONF": "tests.test_preview",
        "CACHES": {
            "default": {
                "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
                "LOCATION": "preview-token-cache-test",
            }
        },
        get_middleware_setting_name(): (
            "mezzanine.core.middleware.UpdateCacheMiddleware",
        )
        + tuple(get_middleware_setting())
        + ("mezzanine.core.middleware.FetchFromCacheMiddleware",),
        "TESTING": False,
        "CACHE_MIDDLEWARE_SECONDS": 60,
    }
)
def test_cache_middleware_does_not_store_preview_response(author_user, client):
    """UpdateCache + FetchFromCache must not store a preview response."""
    cache_installed.cache_clear()
    cache.clear()
    page = RichTextPageFactory(title="Cached Preview Subject")
    raw = PreviewToken.issue(page, created_by=author_user)

    public = client.get("/preview-cache/")
    assert public.status_code == 200
    assert b"no-preview" in public.content
    public_req = RequestFactory().get("/preview-cache/")
    public_key = cache_key_prefix(public_req) + public_req.get_full_path()
    assert cache_get(public_key) is not None

    preview = client.get("/preview-cache/?preview=%s" % raw)
    assert preview.status_code == 200
    assert b"preview-hit" in preview.content
    assert "no-store" in preview["Cache-Control"]
    assert "private" in preview["Cache-Control"]
    preview_req = RequestFactory().get("/preview-cache/?preview=%s" % raw)
    preview_key = cache_key_prefix(preview_req) + preview_req.get_full_path()
    assert cache_get(preview_key) is None

    cache_installed.cache_clear()
