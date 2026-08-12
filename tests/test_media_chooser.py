"""Media chooser popup, FileField widget, Magazine nav."""

from pathlib import Path

import pytest
from django.core.files.storage import default_storage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client
from django.urls import reverse

import mezzanine
from mezzanine.core.fields import FileField
from mezzanine.core.forms import (
    MediaChooserFileWidget,
    MediaChooserFormField,
    _normalize_media_path,
)
from mezzanine.core.models import Media
from tests.factories import SuperUserFactory

REPO = Path(mezzanine.__file__).resolve().parent


@pytest.mark.django_db
def test_media_chooser_popup_lists_assets():
    user = SuperUserFactory(username="chooser", email="c@example.com")
    upload = SimpleUploadedFile(
        "pick.jpg", b"\xff\xd8\xff\xd9", content_type="image/jpeg"
    )
    Media.objects.create(title="Pick me", file=upload, alt="A pickable image")

    client = Client()
    url = reverse("nova_media_chooser")
    assert client.get(url).status_code in (302, 404)

    client.force_login(user)
    resp = client.get(url)
    assert resp.status_code == 200
    body = resp.content.decode("utf-8")
    assert "Pick me" in body
    assert "novaMediaPickerCallback" in body
    assert "novaMediaFieldSelected" in body
    assert "data-path=" in body
    assert "Select" in body

    # Search filter
    resp = client.get(url, {"q": "missing-no-hit"})
    assert resp.status_code == 200
    assert "Pick me" not in resp.content.decode("utf-8")


def test_tinymce_setup_wires_nova_picker():
    js = (REPO / "core/static/mezzanine/js/tinymce_setup.js").read_text(
        encoding="utf-8"
    )
    assert "nova_file_picker" in js
    assert "file_picker_callback" in js
    assert "__nova_media_chooser_url" in js or "nova_media_chooser" in js


def test_filefield_uses_media_chooser_formfield():
    field = FileField(upload_to="tests", blank=True)
    formfield = field.formfield()
    assert isinstance(formfield, MediaChooserFormField)
    assert isinstance(formfield.widget, MediaChooserFileWidget)


def test_normalize_media_path_strips_media_url(settings):
    settings.MEDIA_URL = "/media/"
    assert _normalize_media_path("/media/site-1/a.jpg") == "site-1/a.jpg"
    assert _normalize_media_path("site-1/a.jpg") == "site-1/a.jpg"


@pytest.mark.django_db
def test_media_chooser_formfield_accepts_storage_path():
    name = default_storage.save(
        "media/site-1/chooser-test.jpg",
        SimpleUploadedFile("chooser-test.jpg", b"\xff\xd8\xff\xd9"),
    )
    try:
        field = MediaChooserFormField(required=False)
        cleaned = field.clean(name)
        assert cleaned == name
        with pytest.raises(Exception):
            field.clean("media/site-1/does-not-exist-xyz.jpg")
    finally:
        default_storage.delete(name)


def test_media_chooser_field_assets_exist():
    js = (
        REPO / "core/static/mezzanine/js/admin/media_chooser_field.js"
    ).read_text(encoding="utf-8")
    assert "novaMediaFieldSelected" in js
    assert "nova-media-browse" in js
    css = (
        REPO / "core/static/mezzanine/css/admin/media_chooser_field.css"
    ).read_text(encoding="utf-8")
    assert "nova-media-chooser-widget" in css
    tmpl = (
        REPO / "core/templates/admin/widgets/media_chooser_file.html"
    ).read_text(encoding="utf-8")
    assert "Choose from media library" in tmpl


def test_magazine_nav_includes_blog_link():
    base = (REPO / "kits/magazine/templates/base.html").read_text(encoding="utf-8")
    assert "blog_post_list" in base
    assert "Blog" in base
