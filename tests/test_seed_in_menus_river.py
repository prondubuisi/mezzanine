"""PR-048 / K1+K2: seed in_menus from settings; river uses RIVER_POST_LIMIT."""

from pathlib import Path

import pytest
from django.core.management import call_command

import mezzanine
from mezzanine.conf import settings
from mezzanine.pages.models import RichTextPage
from tests.factories import SuperUserFactory

pytestmark = pytest.mark.django_db
REPO = Path(mezzanine.__file__).resolve().parent


def test_seed_in_menus_matches_page_menu_templates():
    SuperUserFactory(username="admin", email="a@example.com")
    call_command("seed_site_clone", site="techcrunch", flush=True, verbosity=0)
    expected = [str(m[0]) for m in settings.PAGE_MENU_TEMPLATES]
    page = RichTextPage.objects.get(slug="startups")
    assert list(page.in_menus) == expected


def test_recent_posts_template_uses_river_post_limit_setting():
    path = REPO / "kits/shared/templates/includes/recent_posts.html"
    text = path.read_text(encoding="utf-8")
    assert "RIVER_POST_LIMIT" in text
    assert "blog_recent_posts 8" not in text


def test_river_post_limit_is_template_accessible():
    assert "RIVER_POST_LIMIT" in settings.TEMPLATE_ACCESSIBLE_SETTINGS
    assert settings.RIVER_POST_LIMIT == 30
