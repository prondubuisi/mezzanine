"""wordpress.org–inspired kit + seed (WP marketing IA PoC)."""

from pathlib import Path

import pytest
from django.core.management import call_command
from django.test import Client

import mezzanine
from mezzanine.core.models import CONTENT_STATUS_PUBLISHED
from mezzanine.kits.loader import apply_kit, load_kit_meta, validate_kit
from mezzanine.pages.models import RichTextPage
from tests.factories import SuperUserFactory

REPO = Path(mezzanine.__file__).resolve().parent.parent


def test_wporg_kit_meta_and_shared_base():
    root, meta = load_kit_meta("wporg")
    assert meta["name"] == "wporg"
    assert "blog.BlogPost" in meta["types"]
    validate_kit(meta)
    assert (root / "static/wporg/tokens.css").is_file()
    shared = Path(mezzanine.__file__).resolve().parent / "kits/shared/templates"
    assert (shared / "kit_base.html").is_file()
    base = (root / "templates/base.html").read_text(encoding="utf-8")
    assert "kit_base.html" in base
    assert "wporg/tokens.css" in base


def test_apply_wporg_copies_shared_kit_base(tmp_path):
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
    apply_kit("wporg", project, app)
    assert (project / "templates/kit_base.html").is_file()
    assert (project / "templates/base.html").is_file()
    assert (project / "static/wporg/tokens.css").is_file()
    assert "mezzanine.kits.wporg" in (project / app / "settings.py").read_text()
    assert (project / ".nova-kit").read_text().strip() == "wporg"


@pytest.mark.django_db
def test_seed_wporg_demo_creates_ia():
    SuperUserFactory(username="admin", email="a@example.com")
    call_command("seed_wporg_demo", verbosity=0)
    slugs = set(RichTextPage.objects.values_list("slug", flat=True))
    for needed in (
        "features",
        "learn",
        "hosting",
        "community",
        "about",
        "get-started",
    ):
        assert needed in slugs
    features = RichTextPage.objects.get(slug="features")
    assert features.status == CONTENT_STATUS_PUBLISHED
    assert "typed" in features.content.lower() or "Typed" in features.content

    from mezzanine.blog.models import BlogPost

    assert BlogPost.objects.filter(slug="hello-world").exists()
    assert BlogPost.objects.filter(status=CONTENT_STATUS_PUBLISHED).count() >= 3

    # Public pages resolve
    client = Client()
    assert client.get("/features/").status_code == 200
    assert client.get("/get-started/").status_code == 200


@pytest.mark.django_db
def test_import_wporg_inspired_wxr(import_user=None):
    user = SuperUserFactory(username="wpimport", email="w@example.com")
    wxr = REPO / "tests/fixtures/wxr_wporg_inspired.xml"
    assert wxr.is_file()
    call_command(
        "import_wordpress",
        mezzanine_user=user.username,
        url=str(wxr),
        verbosity=0,
        interactive=False,
    )
    assert RichTextPage.objects.filter(slug="features").exists()
    from mezzanine.blog.models import BlogPost

    assert BlogPost.objects.filter(title__icontains="Hello world").exists()


def test_kit_help_lists_wporg():
    help_text = (
        REPO / "mezzanine/bin/management/commands/mezzanine_project.py"
    ).read_text(encoding="utf-8")
    assert "wporg" in help_text


def test_magazine_and_institute_bases_are_thin_wrappers():
    """Redundancy check: kit bases extend shared kit_base."""
    root = Path(mezzanine.__file__).resolve().parent / "kits"
    for name in (
        "magazine",
        "institute",
        "brochure",
        "wporg",
        "whitehouse",
        "techcrunch",
        "time",
    ):
        text = (root / name / "templates/base.html").read_text(encoding="utf-8")
        assert "kit_base.html" in text, name
        assert text.count("<!doctype") == 0
