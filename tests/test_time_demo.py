"""Magazine-shaped TIME-inspired kit — CMS pages/posts + theme."""

from pathlib import Path

import pytest
from django.contrib.auth import get_user_model
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

User = get_user_model()
REPO = Path(mezzanine.__file__).resolve().parent.parent


def test_time_kit_meta():
    root, meta = load_kit_meta("time")
    assert meta["name"] == "time"
    assert kit_wants_blog(meta) is True
    assert kit_seed_profile(meta) == "time"
    validate_kit(meta)
    assert (root / "static/time/tokens.css").is_file()
    assert (root / "templates/index.html").is_file()
    idx = (root / "templates/index.html").read_text(encoding="utf-8")
    assert "includes/recent_posts.html" in idx
    assert "nova-banner" in idx
    theme = load_theme_meta("time")
    assert theme.get("seed_profile") == "time"
    assert profile_theme_map().get("time") == "time"


def test_apply_time_kit(tmp_path):
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
    apply_kit("time", project, app)
    settings = (project / app / "settings.py").read_text(encoding="utf-8")
    assert "mezzanine.kits.time" in settings
    assert "mezzanine.blog" in settings
    assert (project / "static/time/tokens.css").is_file()
    assert (project / ".nova-kit").read_text().strip() == "time"


def test_profile_page_slugs_match_categories():
    profile = get_profile("time")
    page_slugs = {p[1] for p in profile["pages"]}
    from django.utils.text import slugify

    for cat in profile["categories"]:
        assert slugify(cat) in page_slugs, cat


@pytest.mark.django_db
def test_seed_time_sections_list_posts():
    User.objects.create_superuser("admin", "a@example.com", "passwordpassword")
    call_command("seed_site_clone", site="time", flush=True, verbosity=0)

    for slug in (
        "politics",
        "world",
        "business",
        "health",
        "science",
        "ideas",
        "entertainment",
        "about",
    ):
        assert RichTextPage.objects.filter(
            slug=slug, status=CONTENT_STATUS_PUBLISHED
        ).exists(), slug

    assert BlogPost.objects.filter(status=CONTENT_STATUS_PUBLISHED).count() >= 8
    assert BlogCategory.objects.filter(slug="politics").exists()

    client = Client()
    assert client.get("/").status_code == 200

    politics = client.get("/politics/")
    assert politics.status_code == 200
    assert b"leaders" in politics.content.lower() or b"Politics" in politics.content

    ideas = client.get("/ideas/")
    assert ideas.status_code == 200
    assert b"arguing" in ideas.content.lower() or b"Ideas" in ideas.content

    assert client.get("/blog/").status_code == 200
    assert client.get("/contact/").status_code == 200


def test_demo_time_recipe_in_justfile():
    text = (REPO / "justfile").read_text(encoding="utf-8")
    assert "demo-time" in text
    assert (REPO / "mezzanine/project_template/justfile").read_text(
        encoding="utf-8"
    ).find("demo-time") >= 0


def test_time_doc_exists():
    doc = REPO / "docs/modernization/demo-clones/TIME.md"
    assert doc.is_file()
    assert "Horizon" in doc.read_text(encoding="utf-8") or "time" in doc.read_text()
