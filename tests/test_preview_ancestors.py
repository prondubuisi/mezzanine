"""PR-043 / N2: preview ancestor merge uses O(1) parent-map queries."""

import pytest
from django.contrib.auth.models import AnonymousUser
from django.db import connection
from django.test.utils import CaptureQueriesContext

from mezzanine.core.models import CONTENT_STATUS_DRAFT, PreviewToken
from mezzanine.pages.middleware import PageMiddleware
from mezzanine.pages.models import Page
from mezzanine.pages.views import page as page_view
from tests.factories import RichTextPageFactory

pytestmark = pytest.mark.django_db


def test_merge_preview_ancestors_bounded_queries(author_user, rf):
    """
    Deep draft chain: parent walk must not issue one query per level.

    After N2, parent pointers are loaded once for the site, then the
    ancestor objects once — independent of depth.
    """
    parent = None
    slug_parts = []
    # Build a 6-level draft tree under one site.
    for i in range(6):
        slug_parts.append(f"lvl{i}")
        page = RichTextPageFactory(
            title=f"Level {i}",
            slug="/".join(slug_parts),
            parent=parent,
            status=CONTENT_STATUS_DRAFT,
        )
        parent = page
    leaf = parent
    raw = PreviewToken.issue(leaf, created_by=author_user)
    token = PreviewToken.objects.get()

    # Warm contenttypes / site caches outside the measured window.
    Page.objects.with_ascendants_for_slug(leaf.slug, preview=token)

    with CaptureQueriesContext(connection) as ctx:
        pages = Page.objects.with_ascendants_for_slug(leaf.slug, preview=token)
    assert pages
    assert pages[0].pk == leaf.pk
    # Depth is 6; a per-level walk would issue ≥6 parent lookups alone.
    # Budget: published filter + merge (previewed get, parent map, ancestors).
    assert len(ctx.captured_queries) <= 8, [q["sql"] for q in ctx.captured_queries]


def test_deep_draft_chain_still_resolves(author_user, rf):
    """Behavioral lock: previewed deep child still gets draft ancestors."""
    from mezzanine.core.middleware import PreviewTokenMiddleware

    parent = None
    slug_parts = []
    nodes = []
    for i in range(4):
        slug_parts.append(f"deep{i}")
        page = RichTextPageFactory(
            title=f"Deep {i}",
            slug="/".join(slug_parts),
            parent=parent,
            status=CONTENT_STATUS_DRAFT,
        )
        nodes.append(page)
        parent = page
    leaf = nodes[-1]
    raw = PreviewToken.issue(leaf, created_by=author_user)
    request = rf.get(leaf.get_absolute_url() + "?preview=" + raw)
    request.user = AnonymousUser()
    assert PreviewTokenMiddleware(lambda r: None).process_request(request) is None
    response = PageMiddleware(lambda r: None).process_view(request, page_view, [], {})
    assert response is not None
    assert response.status_code == 200
    assert request.page.pk == leaf.pk
    asc = list(request.page.get_ascendants())
    assert [p.pk for p in asc] == [n.pk for n in reversed(nodes[:-1])]
