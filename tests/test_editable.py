"""HTMX ``{% editable %}`` protocol (design §7.2)."""

import pytest
from django.template import RequestContext, Template
from django.urls import reverse

from tests.factories import (
    AuthorFactory,
    BlogPostFactory,
    EditorFactory,
    RichTextPageFactory,
)

pytestmark = pytest.mark.django_db


def _params(obj, fields="title"):
    return {
        "app": obj._meta.app_label,
        "model": obj._meta.object_name.lower(),
        "id": obj.pk,
        "fields": fields,
    }


def _edit_get(client, obj, fields="title", **extra):
    params = _params(obj, fields)
    params.update(extra)
    return client.get(reverse("edit"), params)


def _edit_post(client, obj, fields="title", **values):
    data = _params(obj, fields)
    data.update(values)
    return client.post(reverse("edit"), data, HTTP_HX_REQUEST="true")


def test_edit_get_anonymous_is_403(client):
    page = RichTextPageFactory(title="Anon Edit")
    assert _edit_get(client, page).status_code == 403


def test_edit_get_404_when_missing(client):
    editor = EditorFactory()
    client.force_login(editor)
    page = RichTextPageFactory(title="Gone")
    params = _params(page)
    params["id"] = 999999
    assert client.get(reverse("edit"), params).status_code == 404


def test_edit_get_returns_textarea_form_for_editor(client):
    editor = EditorFactory()
    client.force_login(editor)
    page = RichTextPageFactory(title="Form Title")
    response = _edit_get(client, page)
    assert response.status_code == 200
    body = response.content.decode()
    assert "<textarea" in body
    assert "Form Title" in body
    assert "jquery.form" not in body
    assert "tinymce" not in body.lower()


def test_edit_get_403_for_author_on_page(client):
    author = AuthorFactory()
    client.force_login(author)
    page = RichTextPageFactory(title="Author Page")
    assert _edit_get(client, page).status_code == 403


def test_edit_post_saves_and_returns_island(client):
    editor = EditorFactory()
    client.force_login(editor)
    page = RichTextPageFactory(title="Old Title")
    response = _edit_post(client, page, title="New Title")
    assert response.status_code == 200
    body = response.content.decode()
    assert "New Title" in body
    assert "editable-island" in body
    assert "hx-get" in body
    page.refresh_from_db()
    assert page.title == "New Title"


def test_edit_post_invalid_returns_400_form(client):
    editor = EditorFactory()
    client.force_login(editor)
    page = RichTextPageFactory(title="Keep Me")
    response = _edit_post(client, page, title="")
    assert response.status_code == 400
    assert b"<textarea" in response.content
    page.refresh_from_db()
    assert page.title == "Keep Me"


def test_edit_post_author_saves_own_blog(client):
    author = AuthorFactory()
    client.force_login(author)
    post = BlogPostFactory(title="Mine", user=author)
    response = _edit_post(client, post, title="Still Mine")
    assert response.status_code == 200
    assert b"Still Mine" in response.content
    post.refresh_from_db()
    assert post.title == "Still Mine"


def test_edit_post_author_denied_others_blog(client):
    author = AuthorFactory()
    other = AuthorFactory()
    client.force_login(author)
    post = BlogPostFactory(title="Theirs", user=other)
    response = _edit_post(client, post, title="Stolen")
    assert response.status_code == 403
    post.refresh_from_db()
    assert post.title == "Theirs"


def test_editable_tag_emits_htmx_island(rf):
    editor = EditorFactory()
    page = RichTextPageFactory(title="Island Title")
    request = rf.get("/")
    request.user = editor
    html = Template(
        "{% load mezzanine_tags %}"
        "{% editable page.title %}{{ page.title }}{% endeditable %}"
    ).render(RequestContext(request, {"page": page}))
    assert "editable-island" in html
    assert "hx-get" in html
    assert reverse("edit") in html
    assert "Island Title" in html
    assert "jquery.form" not in html


def test_editable_tag_plain_for_author_on_page(rf):
    author = AuthorFactory()
    page = RichTextPageFactory(title="Just Text")
    request = rf.get("/")
    request.user = author
    html = Template(
        "{% load mezzanine_tags %}"
        "{% editable page.title %}{{ page.title }}{% endeditable %}"
    ).render(RequestContext(request, {"page": page}))
    assert "editable-island" not in html
    assert "Just Text" in html


def test_editable_loader_skips_jquery_form_and_tinymce(rf):
    editor = EditorFactory()
    editor.has_site_permission = True
    request = rf.get("/")
    request.user = editor
    html = Template("{% load mezzanine_tags %}{% editable_loader %}").render(
        RequestContext(request, {"request": request})
    )
    assert "htmx.min.js" in html
    assert "jquery.form" not in html
    assert "jquery.tools" not in html
    assert "tinymce" not in html.lower()
