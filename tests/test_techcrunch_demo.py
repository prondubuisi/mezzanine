"""Tech news desk kit (TechCrunch-shaped IA) — CMS pages/posts + theme."""

from pathlib import Path

import pytest
from django.core.management import call_command
from django.test import Client

import mezzanine
from mezzanine.blog.models import BlogCategory, BlogPost
from mezzanine.core.models import CONTENT_STATUS_PUBLISHED
from mezzanine.demos.site_profiles import get_profile
from mezzanine.kits.loader import (
    apply_kit,
    kit_seed_profile,
    kit_wants_blog,
    load_kit_meta,
    validate_kit,
)
from mezzanine.kits.theme import load_theme_meta, profile_theme_map
from mezzanine.pages.models import RichTextPage
from tests.factories import SuperUserFactory

REPO = Path(mezzanine.__file__).resolve().parent.parent


def test_techcrunch_kit_meta():
    root, meta = load_kit_meta("techcrunch")
    assert meta["name"] == "techcrunch"
    assert kit_wants_blog(meta) is True
    assert kit_seed_profile(meta) == "techcrunch"
    validate_kit(meta)
    assert (root / "static/techcrunch/tokens.css").is_file()
    assert (root / "templates/index.html").is_file()
    idx = (root / "templates/index.html").read_text(encoding="utf-8")
    assert "includes/recent_posts.html" in idx
    assert "nova-banner" in idx
    theme = load_theme_meta("techcrunch")
    assert theme.get("seed_profile") == "techcrunch"
    assert profile_theme_map().get("techcrunch") == "techcrunch"


def test_apply_techcrunch_kit(tmp_path):
    project = tmp_path / "site"
    app = "mysite"
    (project / app).mkdir(parents=True)
    (project / app / "settings.py").write_text(
        "INSTALLED_APPS = [\n"
        '    "django.contrib.admin",\n'
        '    "mezzanine.core",\n'
        '    "mezzanine.pages",\n'
        "]\n"
        'STATIC_ROOT = os.path.join(PROJECT_ROOT, STATIC_URL.strip("/"))\n',
        encoding="utf-8",
    )
    apply_kit("techcrunch", project, app)
    settings = (project / app / "settings.py").read_text(encoding="utf-8")
    assert "mezzanine.kits.techcrunch" in settings
    assert "mezzanine.blog" in settings
    assert (project / "templates/kit_base.html").is_file()
    assert (project / "static/techcrunch/tokens.css").is_file()
    assert (project / ".nova-kit").read_text().strip() == "techcrunch"


def test_profile_page_slugs_match_categories():
    profile = get_profile("techcrunch")
    page_slugs = {p[1] for p in profile["pages"]}
    from django.utils.text import slugify

    for cat in profile["categories"]:
        assert slugify(cat) in page_slugs, cat


@pytest.mark.django_db
def test_seed_techcrunch_sections_list_posts():
    SuperUserFactory(username="admin", email="a@example.com")
    call_command("seed_site_clone", site="techcrunch", flush=True, verbosity=0)

    for slug in ("startups", "venture", "ai", "apps", "security", "events", "about"):
        assert RichTextPage.objects.filter(
            slug=slug, status=CONTENT_STATUS_PUBLISHED
        ).exists(), slug

    assert BlogPost.objects.filter(status=CONTENT_STATUS_PUBLISHED).count() >= 8
    assert BlogCategory.objects.filter(slug="venture").exists()
    assert BlogCategory.objects.filter(slug="ai").exists()

    client = Client()
    assert client.get("/").status_code == 200

    venture = client.get("/venture/")
    assert venture.status_code == 200
    body = venture.content.decode("utf-8")
    assert "Series A" in body or "vertical SaaS" in body

    ai = client.get("/ai/")
    assert ai.status_code == 200
    assert b"device" in ai.content.lower() or b"weights" in ai.content.lower()

    startups = client.get("/startups/")
    assert startups.status_code == 200
    assert b"logistics" in startups.content.lower() or b"Launch" in startups.content

    assert client.get("/blog/").status_code == 200
    assert client.get("/contact/").status_code == 200


def test_demo_techcrunch_recipe_in_justfile():
    text = (REPO / "justfile").read_text(encoding="utf-8")
    assert "demo-techcrunch" in text


def test_techcrunch_doc_exists():
    doc = REPO / "docs/modernization/demo-clones/TECHCRUNCH.md"
    assert doc.is_file()
    assert "techcrunch" in doc.read_text(encoding="utf-8")
