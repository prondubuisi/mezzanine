"""PR-039: role_for_user memoization (DESIGN.md Amendment 2, N1).

Characterization first, then assert single SiteRole query per (user, site)
within a request.
"""

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext

from mezzanine.core.capabilities import (
    CAP_PAGE_EDIT,
    CAP_PREVIEW_ISSUE,
    role_for_user,
    user_has_capability,
)
from mezzanine.core.models import ROLE_AUTHOR, ROLE_EDITOR, ROLE_PUBLISHER
from mezzanine.core.request import current_request
from mezzanine.utils.sites import current_site_id
from tests.factories import AuthorFactory, EditorFactory, PublisherFactory, UserFactory


@pytest.mark.django_db
def test_role_for_user_returns_role_string():
    """Characterization: known roles resolve correctly."""
    author = AuthorFactory()
    editor = EditorFactory()
    publisher = PublisherFactory()
    assert role_for_user(author) == ROLE_AUTHOR
    assert role_for_user(editor) == ROLE_EDITOR
    assert role_for_user(publisher) == ROLE_PUBLISHER
    assert role_for_user(None) is None


@pytest.mark.django_db
def test_role_for_user_none_without_siterole():
    user = UserFactory(username="no-role", email="n@example.com", password="x" * 12)
    assert role_for_user(user) is None


def _bind_request(rf, user):
    """RequestFactory request with session + ContextVar binding."""
    from django.contrib.sessions.backends.db import SessionStore

    from mezzanine.core import request as request_mod

    request = rf.get("/")
    request.user = user
    request.session = SessionStore()
    token = request_mod._current_request.set(request)
    return request, token, request_mod


@pytest.mark.django_db
def test_role_for_user_memoized_on_request(rf):
    """Multiple lookups in one request issue one SiteRole query (N1)."""
    editor = EditorFactory()
    request, token, request_mod = _bind_request(rf, editor)
    try:
        assert current_request() is request
        with CaptureQueriesContext(connection) as ctx:
            for _ in range(10):
                assert role_for_user(editor) == ROLE_EDITOR
                assert user_has_capability(editor, CAP_PAGE_EDIT) is True
                assert user_has_capability(editor, CAP_PREVIEW_ISSUE) is False
        siterole_queries = [
            q
            for q in ctx.captured_queries
            if "core_siterole" in q["sql"].lower()
            or "siterole" in q["sql"].lower()
        ]
        assert len(siterole_queries) == 1, (
            "expected 1 SiteRole query, got %s: %s"
            % (len(siterole_queries), [q["sql"] for q in siterole_queries])
        )
    finally:
        request_mod._current_request.reset(token)


@pytest.mark.django_db
def test_role_for_user_cache_isolated_per_site(rf):
    """Different site_id keys do not share a cached role."""
    from django.contrib.sites.models import Site

    from mezzanine.core.models import SiteRole

    editor = EditorFactory()
    other = Site.objects.create(domain="other.test", name="other")
    SiteRole.objects.create(user=editor, site=other, role=ROLE_PUBLISHER)

    _request, token, request_mod = _bind_request(rf, editor)
    try:
        site1 = current_site_id()
        assert role_for_user(editor, site_id=site1) == ROLE_EDITOR
        assert role_for_user(editor, site_id=other.id) == ROLE_PUBLISHER
        # Second pass still correct (cached independently)
        assert role_for_user(editor, site_id=site1) == ROLE_EDITOR
        assert role_for_user(editor, site_id=other.id) == ROLE_PUBLISHER
    finally:
        request_mod._current_request.reset(token)
