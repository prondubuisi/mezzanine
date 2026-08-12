"""White House–style demo: kit + seed + section post listings."""

from pathlib import Path

import pytest
from django.core.management import call_command
from django.test import Client

import mezzanine
from mezzanine.blog.models import BlogCategory, BlogPost
from mezzanine.core.models import CONTENT_STATUS_PUBLISHED
from mezzanine.demos.site_profiles import get_profile
from mezzanine.kits.loader import apply_kit, load_kit_meta, validate_kit
from mezzanine.pages.models import RichTextPage
from tests.factories import SuperUserFactory

REPO = Path(mezzanine.__file__).resolve().parent.parent


def test_whitehouse_kit_meta():
    from mezzanine.kits.loader import kit_seed_profile, kit_wants_blog

    root, meta = load_kit_meta("whitehouse")
    assert meta["name"] == "whitehouse"
    assert "blog.BlogPost" in meta["types"]
    assert kit_wants_blog(meta) is True
    assert kit_seed_profile(meta) == "whitehouse"
    validate_kit(meta)
    assert (root / "static/whitehouse/tokens.css").is_file()
    assert (root / "templates/index.html").is_file()
    base = (root / "templates/base.html").read_text(encoding="utf-8")
    assert "whitehouse/tokens.css" in base
    assert "/releases/" in base
    idx = (root / "templates/index.html").read_text(encoding="utf-8")
    assert "nova-banner" in idx
    assert "includes/recent_posts.html" in idx


def test_apply_whitehouse_kit(tmp_path):
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
    apply_kit("whitehouse", project, app)
    settings = (project / app / "settings.py").read_text(encoding="utf-8")
    assert "mezzanine.kits.whitehouse" in settings
    assert "mezzanine.blog" in settings
    assert (project / "templates/kit_base.html").is_file()
    assert (project / "templates/includes/recent_posts.html").is_file()
    assert (project / "templates/pages/richtextpage.html").is_file()
    assert (project / "static/whitehouse/tokens.css").is_file()
    assert (project / ".nova-kit").read_text().strip() == "whitehouse"


def test_profile_page_slugs_match_categories():
    profile = get_profile("whitehouse")
    page_slugs = {p[1] for p in profile["pages"]}
    from django.utils.text import slugify

    for cat in profile["categories"]:
        assert slugify(cat) in page_slugs, cat


@pytest.mark.django_db
def test_seed_whitehouse_section_lists_posts():
    SuperUserFactory(username="admin", email="a@example.com")
    call_command("seed_site_clone", site="whitehouse", flush=True, verbosity=0)

    for slug in (
        "releases",
        "briefings",
        "presidential-actions",
        "nominations",
        "administration",
        "priorities",
        "about",
    ):
        assert RichTextPage.objects.filter(
            slug=slug, status=CONTENT_STATUS_PUBLISHED
        ).exists(), slug

    assert BlogPost.objects.filter(status=CONTENT_STATUS_PUBLISHED).count() >= 8
    assert BlogCategory.objects.filter(slug="releases").exists()

    client = Client()
    home = client.get("/")
    assert home.status_code == 200

    # Section page should include posts via page processor.
    resp = client.get("/releases/")
    assert resp.status_code == 200
    body = resp.content.decode("utf-8")
    assert "Statement on infrastructure progress" in body
    assert "section-posts" in body or "Browse" in body or "infrastructure" in body

    briefings = client.get("/briefings/")
    assert briefings.status_code == 200
    assert b"Press briefing" in briefings.content or b"briefing" in briefings.content

    actions = client.get("/presidential-actions/")
    assert actions.status_code == 200
    assert b"energy" in actions.content.lower() or b"Executive" in actions.content

    assert client.get("/blog/").status_code == 200
    assert client.get("/contact/").status_code == 200


def test_kit_help_lists_whitehouse():
    help_text = (
        REPO / "mezzanine/bin/management/commands/mezzanine_project.py"
    ).read_text(encoding="utf-8")
    assert "whitehouse" in help_text


def test_demo_whitehouse_recipe_in_justfile():
    text = (REPO / "justfile").read_text(encoding="utf-8")
    assert "demo-whitehouse" in text
    assert "whitehouse" in text
