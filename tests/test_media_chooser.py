"""Media chooser popup and Magazine nav (WP media-modal / primary-nav parity)."""

from pathlib import Path

import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client
from django.urls import reverse

import mezzanine
from mezzanine.core.models import Media

User = get_user_model()
REPO = Path(mezzanine.__file__).resolve().parent


@pytest.mark.django_db
def test_media_chooser_popup_lists_assets():
    user = User.objects.create_superuser(
        "chooser", "c@example.com", "passwordpassword"
    )
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


def test_magazine_nav_includes_blog_link():
    base = (REPO / "kits/magazine/templates/base.html").read_text(encoding="utf-8")
    assert "blog_post_list" in base
    assert "Blog" in base
