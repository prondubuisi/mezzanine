"""PR-049 / K3+K4: kit nav from site_profiles; tokens from theme.json."""

import pytest
from django.urls import reverse

from mezzanine.kits.theme import (
    set_active_theme,
    theme_nav_items,
    theme_tokens_static,
)

pytestmark = pytest.mark.django_db


def test_theme_tokens_static_from_theme_json():
    set_active_theme("techcrunch")
    assert theme_tokens_static() == "techcrunch/tokens.css"
    set_active_theme("time")
    assert theme_tokens_static() == "time/tokens.css"


def test_theme_primary_nav_matches_site_profile_categories():
    set_active_theme("techcrunch")
    items = theme_nav_items("primary")
    titles = [i["title"] for i in items]
    assert titles[0] == "Latest"
    assert items[0]["href"] == reverse("blog_post_list")
    # Category sections from site_profiles, not hand-typed template links.
    assert "Startups" in titles
    assert "Venture" in titles
    assert "AI" in titles
    assert "/startups/" in [i["href"] for i in items]
    # About is a page but not a category — not in primary.
    assert "About" not in titles


def test_theme_footer_nav_includes_pages_and_contact():
    set_active_theme("techcrunch")
    items = theme_nav_items("footer")
    hrefs = [i["href"] for i in items]
    assert "/startups/" in hrefs
    assert "/about/" in hrefs
    assert "/contact/" in hrefs
    assert reverse("blog_post_list") in hrefs


def test_newsroom_kit_bases_are_thin_wrappers():
    """K3: techcrunch/time/whitehouse base.html no longer hardcode section slugs."""
    from pathlib import Path

    import mezzanine

    root = Path(mezzanine.__file__).resolve().parent / "kits"
    for name in ("techcrunch", "time", "whitehouse"):
        text = (root / name / "templates/base.html").read_text(encoding="utf-8")
        assert 'extends "kit_base.html"' in text
        assert "/startups/" not in text
        assert "/politics/" not in text
        assert "/releases/" not in text
        assert "kit_primary_nav" not in text
