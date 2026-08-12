"""Spotify Newsroom–style demo: kit + seed + section post listings + full flow."""

from pathlib import Path

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import Client

import mezzanine
from mezzanine.blog.models import BlogCategory, BlogPost
from mezzanine.core.models import CONTENT_STATUS_PUBLISHED
from mezzanine.demos.site_profiles import get_profile
from mezzanine.forms.models import Field, Form
from mezzanine.kits.loader import (
    apply_kit,
    kit_seed_profile,
    kit_wants_blog,
    load_kit_meta,
    validate_kit,
)
from mezzanine.pages.models import RichTextPage

User = get_user_model()
REPO = Path(mezzanine.__file__).resolve().parent.parent

# Public browsing path for the newsroom demo (home → section → story → press → contact).
SPOTIFY_FLOW = (
    "/",
    "/company-news/",
    "/product-features/",
    "/culture/",
    "/creators/",
    "/policy/",
    "/for-the-press/",
    "/about/",
    "/blog/",
    "/blog/new-listening-feature/",
    "/contact/",
)


def test_spotify_kit_meta():
    root, meta = load_kit_meta("spotify")
    assert meta["name"] == "spotify"
    assert "blog.BlogPost" in meta["types"]
    assert kit_wants_blog(meta) is True
    assert kit_seed_profile(meta) == "spotify_newsroom"
    validate_kit(meta)
    assert (root / "static/spotify/tokens.css").is_file()
    assert (root / "templates/index.html").is_file()
    base = (root / "templates/base.html").read_text(encoding="utf-8")
    assert "spotify/tokens.css" in base
    assert "/company-news/" in base
    idx = (root / "templates/index.html").read_text(encoding="utf-8")
    assert "includes/recent_posts.html" in idx
    assert "nova-banner" in idx
    assert "nova-grid" in idx


def test_apply_spotify_kit(tmp_path):
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
    apply_kit("spotify", project, app)
    settings = (project / app / "settings.py").read_text(encoding="utf-8")
    assert "mezzanine.kits.spotify" in settings
    assert "mezzanine.blog" in settings
    assert (project / "templates/kit_base.html").is_file()
    assert (project / "templates/includes/recent_posts.html").is_file()
    assert (project / "templates/pages/richtextpage.html").is_file()
    assert (project / "static/spotify/tokens.css").is_file()
    assert (project / "static/nova_kits/newsroom.css").is_file()
    assert (project / ".nova-kit").read_text().strip() == "spotify"
    kit_base = (project / "templates/kit_base.html").read_text(encoding="utf-8")
    assert "nova_kits/newsroom.css" in kit_base


def test_profile_page_slugs_match_categories():
    profile = get_profile("spotify_newsroom")
    page_slugs = {p[1] for p in profile["pages"]}
    from django.utils.text import slugify

    for cat in profile["categories"]:
        assert slugify(cat) in page_slugs, cat


@pytest.mark.django_db
def test_seed_spotify_section_lists_posts():
    User.objects.create_superuser("admin", "a@example.com", "passwordpassword")
    call_command("seed_site_clone", site="spotify_newsroom", flush=True, verbosity=0)

    for slug in (
        "company-news",
        "product-features",
        "culture",
        "creators",
        "policy",
        "for-the-press",
        "about",
    ):
        assert RichTextPage.objects.filter(
            slug=slug, status=CONTENT_STATUS_PUBLISHED
        ).exists(), slug

    assert BlogPost.objects.filter(status=CONTENT_STATUS_PUBLISHED).count() >= 8
    assert BlogCategory.objects.filter(slug="company-news").exists()
    assert BlogCategory.objects.filter(slug="product-features").exists()

    client = Client()
    home = client.get("/")
    assert home.status_code == 200

    resp = client.get("/company-news/")
    assert resp.status_code == 200
    body = resp.content.decode("utf-8")
    assert "regional studio" in body.lower() or "Company" in body
    assert "section-posts" in body or "Browse" in body or "transparency" in body.lower()

    product = client.get("/product-features/")
    assert product.status_code == 200
    assert b"listening" in product.content.lower() or b"Product" in product.content

    culture = client.get("/culture/")
    assert culture.status_code == 200
    assert b"build in public" in culture.content or b"Mentorship" in culture.content

    assert client.get("/blog/").status_code == 200
    assert client.get("/contact/").status_code == 200
    assert client.get("/for-the-press/").status_code == 200


def test_kit_help_lists_spotify():
    help_text = (
        REPO / "mezzanine/bin/management/commands/mezzanine_project.py"
    ).read_text(encoding="utf-8")
    assert "spotify" in help_text


def test_demo_spotify_recipe_in_justfile():
    text = (REPO / "justfile").read_text(encoding="utf-8")
    assert "demo-spotify" in text
    assert "spotify_newsroom" in text


def test_spotify_doc_exists():
    doc = REPO / "docs/modernization/demo-clones/SPOTIFY.md"
    assert doc.is_file()
    text = doc.read_text(encoding="utf-8")
    assert "spotify" in text
    assert "seed_profile" in text
    assert "Demo flow" in text or "flow" in text.lower()


def test_shared_story_template_exists():
    path = (
        Path(mezzanine.__file__).resolve().parent
        / "kits/shared/templates/blog/blog_post_detail.html"
    )
    assert path.is_file()
    text = path.read_text(encoding="utf-8")
    assert "nova-story-nav" in text
    assert "blog_post_list" in text


def test_apply_spotify_copies_story_template(tmp_path):
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
    apply_kit("spotify", project, app)
    story = project / "templates/blog/blog_post_detail.html"
    assert story.is_file()
    assert "nova-story-nav" in story.read_text(encoding="utf-8")
    footer = (project / "templates/base.html").read_text(encoding="utf-8")
    assert "footer-links" in footer
    assert "/for-the-press/" in footer


@pytest.mark.django_db
def test_spotify_demo_end_to_end_flow():
    """
    Full public content flow: sections → story → category → press → contact.

    Chrome classes (nova-banner, etc.) require a project built with ``--kit spotify``;
    package tests use the default template project, so this asserts the IA + forms path.
    """
    User.objects.create_superuser("admin", "a@example.com", "passwordpassword")
    call_command("seed_site_clone", site="spotify_newsroom", flush=True, verbosity=0)
    client = Client()

    for path in SPOTIFY_FLOW:
        resp = client.get(path)
        assert resp.status_code == 200, path

    # Section lists the seeded company post (processor and/or category link).
    company = client.get("/company-news/").content.decode("utf-8")
    assert "studio partnership" in company.lower() or "transparency" in company.lower()
    assert "Browse" in company or "Company News" in company or "section" in company.lower()

    # Story body from seed.
    story = client.get("/blog/new-listening-feature/").content.decode("utf-8")
    assert "listening" in story.lower()
    assert "Product" in story or "product" in story.lower()

    # Category archive (blog filter).
    cat = client.get("/blog/category/product-features/")
    assert cat.status_code == 200
    assert b"listening" in cat.content.lower() or b"roadmap" in cat.content.lower()

    # Press hub points at contact.
    press = client.get("/for-the-press/").content.decode("utf-8")
    assert "/contact/" in press

    # Contact form submit → thank-you (sent=1).
    form_page = Form.objects.get(slug="contact")
    fields = list(Field.objects.filter(form=form_page).order_by("_order", "id"))
    assert len(fields) >= 2
    data = {f"field_{fields[0].id}": "press@example.com"}
    data[f"field_{fields[1].id}"] = "Requesting a demo press kit."
    posted = client.post("/contact/", data)
    assert posted.status_code in (200, 302)
    if posted.status_code == 302:
        assert "sent=1" in posted["Location"] or "sent=1" in getattr(
            posted, "url", ""
        )
        loc = posted["Location"] if "Location" in posted else posted.url
        thanks = client.get(loc)
    else:
        thanks = client.get("/contact/?sent=1")
    assert thanks.status_code == 200
    body = thanks.content.decode("utf-8")
    assert "Thanks" in body or "received" in body.lower()
