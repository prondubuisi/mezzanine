"""Y1.5: document body (025), Media (026), healthz (036b), TinyMCE (028)."""

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client
from django.urls import reverse

from mezzanine.core.document import (
    SCHEMA_ID,
    body_from_html,
    html_from_body,
    normalize_body,
)
from mezzanine.core.models import Media
from mezzanine.pages.models import RichTextPage
from tests.factories import SuperUserFactory


def test_body_schema_roundtrip():
    body = body_from_html("<p>Hello</p>")
    assert body["$schema"] == SCHEMA_ID
    assert html_from_body(body) == "<p>Hello</p>"
    assert normalize_body(body)["blocks"][0]["type"] == "html"


def test_body_rejects_unknown_block_types():
    with pytest.raises(ValueError, match="v1 schema"):
        normalize_body(
            {
                "$schema": SCHEMA_ID,
                "blocks": [{"type": "figure", "html": "x"}],
            }
        )


@pytest.mark.django_db
def test_richtextpage_body_syncs_content():
    page = RichTextPage.objects.create(
        title="Body Page",
        content="<p>from content</p>",
    )
    page.refresh_from_db()
    assert page.body["$schema"] == SCHEMA_ID
    assert "from content" in html_from_body(page.body)
    assert "from content" in page.content

    page.body = body_from_html("<p>from body</p>")
    page.save()
    page.refresh_from_db()
    assert page.content == "<p>from body</p>"


@pytest.mark.django_db
def test_media_requires_alt_and_site_prefix(settings):
    user = SuperUserFactory(username="admin", email="a@example.com")
    upload = SimpleUploadedFile(
        "shot.jpg", b"\xff\xd8\xff\xd9", content_type="image/jpeg"
    )
    asset = Media.objects.create(title="Shot", file=upload, alt="A photo")
    assert asset.alt == "A photo"
    assert f"site-{asset.site_id}" in asset.file.name
    assert asset.is_public is False
    url = reverse("nova_media_detail", kwargs={"pk": asset.pk})
    assert asset.get_absolute_url() == url

    client = Client()
    assert client.get(url).status_code in (302, 404)
    # Private by default — public endpoint 404s for anonymous.
    pub = reverse("nova_media_public", kwargs={"pk": asset.pk})
    assert client.get(pub).status_code == 404

    client.force_login(user)
    resp = client.get(url)
    assert resp.status_code == 200
    data = resp.json()
    assert data["alt"] == "A photo"
    assert data["id"] == asset.pk
    assert data["is_public"] is False

    listing = client.get(reverse("nova_media_list"))
    assert listing.status_code == 200
    body = listing.json()
    assert body["ok"] is True
    assert any(item["id"] == asset.pk for item in body["results"])

    # Promote to public metadata (still not Displayable / sitemap).
    asset.is_public = True
    asset.save()
    assert asset.get_absolute_url() == pub
    anon = Client()
    public_resp = anon.get(pub)
    assert public_resp.status_code == 200
    assert public_resp.json()["is_public"] is True
    assert public_resp.json()["alt"] == "A photo"


@pytest.mark.django_db
def test_healthz_ok(client):
    resp = client.get(reverse("nova_healthz"))
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["db"] is True
    assert data["service"] == "nova-cms"


def test_tinymce4_static_tree_removed():
    from pathlib import Path

    import mezzanine

    root = Path(mezzanine.__file__).resolve().parent
    assert not (root / "core/static/mezzanine/tinymce").exists()


def test_default_richtext_widget_is_textarea():
    from mezzanine.conf import settings

    assert "AdminTextareaWidget" in settings.RICHTEXT_WIDGET_CLASS


@pytest.mark.django_db
def test_api_resolve_and_openapi():
    user = SuperUserFactory(username="apiadmin", email="api@example.com")
    page = RichTextPage.objects.create(
        title="Resolve Me",
        content="<p>hi</p>",
        status=2,  # published
    )
    # Ensure published status constant
    from mezzanine.core.models import CONTENT_STATUS_PUBLISHED

    page.status = CONTENT_STATUS_PUBLISHED
    page.save()
    client = Client()
    # Anonymous → 404 (no existence leak)
    assert client.get(reverse("nova_api_resolve"), {"path": "/"}).status_code in (
        302,
        404,
    )
    client.force_login(user)
    openapi = client.get(reverse("nova_api_openapi"))
    assert openapi.status_code == 200
    assert openapi.json()["openapi"].startswith("3.")
    # Resolve by slug path if available
    path = page.get_absolute_url()
    resp = client.get(reverse("nova_api_resolve"), {"path": path})
    # url_map may or may not include draft-default pages; publish first
    if resp.status_code == 404:
        # publish and retry
        page.status = CONTENT_STATUS_PUBLISHED
        page.save()
        resp = client.get(reverse("nova_api_resolve"), {"path": path})
    assert resp.status_code == 200, resp.content
    data = resp.json()
    assert data["ok"] is True
    assert data["id"] == page.pk
    assert "Resolve" in data["title"]
