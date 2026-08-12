"""Adult WordPress importer (PR-035)."""

import json
import re
from pathlib import Path

import pytest
from django.contrib.auth import get_user_model
from django.contrib.redirects.models import Redirect
from django.core.management import call_command
from django.core.management.base import CommandError

import mezzanine
from mezzanine.blog.models import BlogPost
from mezzanine.core.models import CONTENT_STATUS_DRAFT, CONTENT_STATUS_PUBLISHED
from mezzanine.migrate.report import MigrationReport
from mezzanine.pages.models import Page, RichTextPage

REPO_ROOT = Path(mezzanine.__file__).resolve().parent.parent
WXR = REPO_ROOT / "tests" / "fixtures" / "wxr_sample.xml"
User = get_user_model()


@pytest.fixture
def import_user(db):
    return User.objects.create_superuser(
        "admin", "admin@example.com", "passwordpassword"
    )


@pytest.mark.django_db
def test_import_wordpress_requires_user():
    with pytest.raises(CommandError, match="No Mezzanine user"):
        call_command("import_wordpress", url=str(WXR), verbosity=0)


@pytest.mark.django_db
def test_import_wordpress_requires_url(import_user):
    with pytest.raises(CommandError, match="--url"):
        call_command(
            "import_wordpress",
            mezzanine_user=import_user.username,
            verbosity=0,
        )


@pytest.mark.django_db
def test_import_wordpress_sample_wxr(import_user, capsys):
    call_command(
        "import_wordpress",
        mezzanine_user=import_user.username,
        url=str(WXR),
        verbosity=1,
        interactive=False,
    )
    out = capsys.readouterr().out

    published = BlogPost.objects.get(title="Hello World")
    assert published.status == CONTENT_STATUS_PUBLISHED
    assert published._meta_title == "Hello SEO Title"
    assert published.description == "Hello SEO description"
    assert "First post body" in published.content
    assert published.categories.filter(title="News").exists()
    # Attachment id 20 + _thumbnail_id → BlogPost.featured_image (A0 FileField).
    assert published.featured_image
    assert published.featured_image.name.endswith("hero.jpg")

    draft = BlogPost.objects.get(title="Draft Only")
    assert draft.status == CONTENT_STATUS_DRAFT
    assert not draft.featured_image

    about = RichTextPage.objects.get(title="About")
    assert about.status == CONTENT_STATUS_PUBLISHED
    assert about._meta_title == "About SEO"
    assert about.description == "About meta description"

    team = RichTextPage.objects.get(title="Team")
    assert team.parent_id == about.id
    assert team.slug.endswith("about/team") or "team" in team.slug

    # Permalinks become redirects.
    assert Redirect.objects.filter(old_path="/hello-world/").exists()
    assert Redirect.objects.filter(old_path="/about/").exists()
    assert Redirect.objects.filter(old_path="/about/team/").exists()

    # Report covers fidelity, unmapped types, attachments (text + JSON).
    assert "migration report" in out.lower() or "Posts imported" in out
    assert "product" in out
    assert BlogPost.objects.filter(title="Custom Product").count() == 0
    assert not Page.objects.filter(title="Hero Image").exists()
    # KD15: machine JSON is printed after the human summary.
    payload = _last_json_object(out)
    assert payload["posts_imported"] >= 1
    assert payload["pages_imported"] >= 1
    assert payload["redirects_created"] >= 1
    assert payload["attachments_imported"] >= 1
    assert "product" in payload["unmapped_types"]
    assert any(pair["old"] for pair in payload["url_fidelity"])

def _last_json_object(text: str) -> dict:
    """Parse the trailing one-line JSON object from command stdout."""
    for line in reversed(text.splitlines()):
        line = line.strip()
        if line.startswith("{") and line.endswith("}"):
            return json.loads(line)
    raise AssertionError("expected JSON report line in stdout")


@pytest.mark.django_db
def test_import_wordpress_report_json_file(import_user, tmp_path):
    report_path = tmp_path / "migration.json"
    call_command(
        "import_wordpress",
        mezzanine_user=import_user.username,
        url=str(WXR),
        report_json=str(report_path),
        verbosity=0,
        interactive=False,
    )
    data = json.loads(report_path.read_text(encoding="utf-8"))
    assert data["posts_imported"] >= 1
    assert data["pages_imported"] >= 1
    assert "url_fidelity" in data
    assert isinstance(data["unmapped_types"], dict)


def test_migration_report_json_shape():
    report = MigrationReport(
        posts_imported=1,
        pages_imported=2,
        comments_imported=4,
        attachments_imported=1,
    )
    report.note_unmapped("product")
    report.note_redirect("https://example.com/a/", "/a/")
    report.note_attachment_failure("attachment not imported: x.jpg")
    report.skipped.append("posts skipped")
    data = report.to_dict()
    assert data == {
        "posts_imported": 1,
        "pages_imported": 2,
        "comments_imported": 4,
        "redirects_created": 1,
        "attachments_imported": 1,
        "unmapped_types": {"product": 1},
        "failed_attachments": ["attachment not imported: x.jpg"],
        "skipped": ["posts skipped"],
        "url_fidelity": [{"old": "https://example.com/a/", "new": "/a/"}],
    }
    assert json.loads(report.to_json(indent=None)) == data


@pytest.mark.django_db
def test_import_wordpress_skip_attachments(import_user):
    call_command(
        "import_wordpress",
        mezzanine_user=import_user.username,
        url=str(WXR),
        skip_attachments=True,
        verbosity=0,
        interactive=False,
    )
    published = BlogPost.objects.get(title="Hello World")
    assert not published.featured_image


@pytest.mark.django_db
def test_import_wordpress_page_tree_order(import_user):
    call_command(
        "import_wordpress",
        mezzanine_user=import_user.username,
        url=str(WXR),
        verbosity=0,
        interactive=False,
    )
    about = Page.objects.get(title="About")
    team = Page.objects.get(title="Team")
    assert team.parent_id == about.pk


@pytest.mark.django_db
def test_wp_caption_filter():
    from mezzanine.migrate.management.commands.import_wordpress import Command

    raw = (
        '[caption id="attachment_1" align="alignnone" width="300" '
        'caption="A cat"]<img src="c.jpg" />[/caption]'
    )
    html = Command().wp_caption(raw)
    assert "wp-caption" in html
    assert "A cat" in html
    assert "<img src=\"c.jpg\" />" in html


def test_feedparser_in_migrate_extra():
    text = (REPO_ROOT / "pyproject.toml").read_text()
    # migrate extra pins feedparser; testing extra does too so CI can import.
    assert re.search(r"^migrate\s*=\s*\[", text, re.M)
    migrate_block = text.split("migrate = [", 1)[1].split("]", 1)[0]
    assert "feedparser" in migrate_block


def test_migrate_app_packaged():
    cmd = REPO_ROOT / "mezzanine/migrate/management/commands/import_wordpress.py"
    assert cmd.is_file()
    assert (REPO_ROOT / "mezzanine/migrate/base.py").is_file()
    assert (REPO_ROOT / "mezzanine/migrate/report.py").is_file()
