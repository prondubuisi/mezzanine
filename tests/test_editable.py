"""Characterization of today's POST /edit/ (design §7.1).

PR-027 rewrite flips these to the HTMX GET/POST protocol in §7.2.
"""

import pytest
from django.urls import reverse

from tests.factories import (
    AuthorFactory,
    BlogPostFactory,
    EditorFactory,
    RichTextPageFactory,
)

pytestmark = pytest.mark.django_db


def _edit_post(client, obj, fields, **values):
    data = {
        "app": obj._meta.app_label,
        "model": obj._meta.object_name.lower(),
        "id": obj.pk,
        "fields": fields,
    }
    data.update(values)
    return client.post(reverse("edit"), data)


def test_edit_post_redirects_anonymous(client):
    page = RichTextPageFactory(title="Anon Edit")
    response = _edit_post(client, page, "title", title="Nope")
    assert response.status_code == 302
    assert "login" in response["Location"]


def test_edit_post_permission_denied_for_author_on_page(client):
    author = AuthorFactory()
    client.force_login(author)
    page = RichTextPageFactory(title="Author Page")
    response = _edit_post(client, page, "title", title="Hacked")
    assert response.status_code == 200
    assert response.content.decode() == "Permission denied"
    page.refresh_from_db()
    assert page.title == "Author Page"


def test_edit_post_valid_saves_and_returns_empty(client):
    editor = EditorFactory()
    client.force_login(editor)
    page = RichTextPageFactory(title="Old Title")
    response = _edit_post(client, page, "title", title="New Title")
    assert response.status_code == 200
    assert response.content == b""
    page.refresh_from_db()
    assert page.title == "New Title"


def test_edit_post_invalid_returns_first_error_string(client):
    editor = EditorFactory()
    client.force_login(editor)
    page = RichTextPageFactory(title="Keep Me")
    response = _edit_post(client, page, "title", title="")
    assert response.status_code == 200
    assert response.content
    assert b"required" in response.content.lower() or response.content.decode()
    page.refresh_from_db()
    assert page.title == "Keep Me"


def test_edit_post_author_saves_own_blog(client):
    author = AuthorFactory()
    client.force_login(author)
    post = BlogPostFactory(title="Mine", user=author)
    response = _edit_post(client, post, "title", title="Still Mine")
    assert response.status_code == 200
    assert response.content == b""
    post.refresh_from_db()
    assert post.title == "Still Mine"
