"""IA site clones: profiles + seed_site_clone for six public-site shapes."""

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import Client

from mezzanine.blog.models import BlogPost
from mezzanine.core.models import CONTENT_STATUS_PUBLISHED
from mezzanine.demos.site_profiles import PROFILES, get_profile, list_sites
from mezzanine.pages.models import RichTextPage

User = get_user_model()

ALL_SITES = (
    "techcrunch",
    "time",
    "whitehouse",
    "harvard_gazette",
    "ted_blog",
    "spotify_newsroom",
)


def test_all_expected_profiles_registered():
    for slug in ALL_SITES:
        assert slug in PROFILES
        profile = get_profile(slug)
        assert profile["pages"]
        assert profile["posts"]
        assert profile["inspired_by"].startswith("http")
        assert profile["notes"], "each profile must document parity gaps"


def test_list_sites_sorted():
    assert list_sites() == sorted(ALL_SITES)


@pytest.mark.django_db
@pytest.mark.parametrize("slug", ALL_SITES)
def test_seed_each_site_clone(slug):
    User.objects.create_superuser("admin", "a@example.com", "passwordpassword")
    call_command("seed_site_clone", site=slug, verbosity=0, flush=True)
    profile = get_profile(slug)
    for title, page_slug, _html in profile["pages"]:
        page = RichTextPage.objects.get(slug=page_slug)
        assert page.status == CONTENT_STATUS_PUBLISHED
        assert page.title == title
    for title, post_slug, _cat, _html in profile["posts"]:
        post = BlogPost.objects.get(slug=post_slug)
        assert post.status == CONTENT_STATUS_PUBLISHED
        assert post.title == title
    # Public page resolves
    client = Client()
    first_slug = profile["pages"][0][1]
    assert client.get(f"/{first_slug}/").status_code == 200
    assert client.get("/blog/").status_code == 200


@pytest.mark.django_db
def test_seed_unknown_site_errors():
    with pytest.raises(CommandError):
        call_command("seed_site_clone", site="not-a-site", verbosity=0)


def test_parity_backlog_doc_exists():
    from pathlib import Path

    import mezzanine

    root = Path(mezzanine.__file__).resolve().parent.parent
    doc = root / "docs/modernization/demo-clones/PARITY-BACKLOG.md"
    assert doc.is_file()
    text = doc.read_text(encoding="utf-8")
    for slug in ALL_SITES:
        assert slug in text
    assert "X1" in text and "B5" in text
