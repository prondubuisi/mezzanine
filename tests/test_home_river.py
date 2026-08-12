"""Lean homepage river (X1) and section→category links (X2)."""

from pathlib import Path

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import Client, override_settings

import mezzanine
from mezzanine.pages.models import RichTextPage

User = get_user_model()
REPO = Path(mezzanine.__file__).resolve().parent


def test_shared_recent_posts_include_exists():
    path = REPO / "kits/shared/templates/includes/recent_posts.html"
    assert path.is_file()
    text = path.read_text(encoding="utf-8")
    assert "blog_recent_posts" in text


def test_kit_indexes_include_river():
    # Editorial kits use index.html river; listening theme uses music/home.html.
    for name in ("wporg", "magazine", "institute", "whitehouse"):
        idx = (REPO / "kits" / name / "templates/index.html").read_text(
            encoding="utf-8"
        )
        assert "includes/recent_posts.html" in idx, name


def test_shared_newsroom_css_exists():
    path = REPO / "kits/shared/static/nova_kits/newsroom.css"
    assert path.is_file()
    text = path.read_text(encoding="utf-8")
    assert ".nova-banner" in text
    assert ".nova-grid" in text
    assert ".nova-card" in text


@pytest.mark.django_db
def test_time_politics_section_links_category():
    User.objects.create_superuser("admin", "a@example.com", "passwordpassword")
    call_command("seed_site_clone", site="time", flush=True, verbosity=0)
    politics = RichTextPage.objects.get(slug="politics")
    assert "/blog/category/politics/" in politics.content


@pytest.mark.django_db
@override_settings(DEBUG=False)
def test_demo_sites_hidden_when_not_debug():
    client = Client()
    assert client.get("/_nova/demo-sites/").status_code == 404


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_demo_sites_open_when_debug():
    client = Client()
    resp = client.get("/_nova/demo-sites/")
    assert resp.status_code == 200
    assert b"techcrunch" in resp.content
