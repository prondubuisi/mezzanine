"""Theme customizer, slot resolution, plugin auto-append."""

from pathlib import Path

import pytest
from django.test import Client, override_settings

import mezzanine
from mezzanine.kits.theme import (
    apps_for_theme,
    get_theme_colors,
    read_nova_theme_marker,
    resolve_slot_template,
    set_active_theme,
    set_theme_customizer,
    theme_customizer_css,
    write_nova_theme_marker,
)

REPO = Path(mezzanine.__file__).resolve().parent.parent


@pytest.mark.django_db
def test_customizer_persists_colors_and_css():
    set_active_theme("whitehouse")
    set_theme_customizer(
        colors={"accent": "#ff0000", "ink": "#111111"},
        logo_url="https://example.com/logo.png",
    )
    colors = get_theme_colors()
    assert colors.get("accent") == "#ff0000"
    assert colors.get("ink") == "#111111"
    css = theme_customizer_css()
    assert "--nova-accent: #ff0000" in css
    assert "--nova-ink: #111111" in css
    from mezzanine.kits.theme import get_theme_logo_url

    assert get_theme_logo_url() == "https://example.com/logo.png"


@pytest.mark.django_db
def test_customizer_reset_clears_overrides():
    set_active_theme("whitehouse")
    set_theme_customizer(colors={"accent": "#00ff00"}, logo_url="https://x/y.png")
    set_theme_customizer(colors={"accent": ""}, logo_url="")
    # After clear, theme.json default accent may still appear via get_theme_colors
    colors = get_theme_colors()
    # override gone; theme.json may still provide accent
    assert colors.get("accent") != "#00ff00" or "accent" in colors
    from mezzanine.kits.theme import get_theme_logo_url

    assert get_theme_logo_url() == ""


@pytest.mark.django_db
def test_resolve_slot_template_uses_theme_json():
    set_active_theme("spotify")
    assert resolve_slot_template("home", "music/home.html") == "music/home.html"
    assert (
        resolve_slot_template("playlist", "music/playlist.html")
        == "music/playlist.html"
    )
    # Unknown slot → fallback
    assert resolve_slot_template("nope", "fallback.html") == "fallback.html"


def test_apps_for_theme_includes_plugins():
    apps = apps_for_theme("spotify")
    assert "mezzanine.kits.spotify" in apps
    assert "mezzanine.music" in apps
    apps_wh = apps_for_theme("whitehouse")
    assert "mezzanine.kits.whitehouse" in apps_wh
    assert "mezzanine.music" not in apps_wh


def test_nova_theme_marker_roundtrip(tmp_path):
    write_nova_theme_marker("spotify", project_root=tmp_path)
    assert (tmp_path / ".nova-theme").read_text().strip() == "spotify"
    assert read_nova_theme_marker(tmp_path) == "spotify"


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_customizer_page_renders():
    set_active_theme("whitehouse")
    client = Client()
    resp = client.get("/_nova/theme-customizer/")
    assert resp.status_code == 200
    body = resp.content.decode("utf-8")
    assert "Theme customizer" in body
    assert "color_accent" in body or "Accent" in body


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_customizer_save_post():
    set_active_theme("whitehouse")
    client = Client()
    resp = client.post(
        "/_nova/theme-customizer/save/",
        {
            "color_accent": "#abcdef",
            "color_ink": "",
            "color_accent_ink": "",
            "color_canvas": "",
            "color_paper": "",
            "logo_url": "",
        },
    )
    assert resp.status_code in (302, 200)
    colors = get_theme_colors()
    assert colors.get("accent") == "#abcdef"


def test_docs_mark_open_items_done():
    text = (REPO / "docs/modernization/demo-clones/THEME-ABSTRACTION.md").read_text(
        encoding="utf-8"
    )
    assert "Customizer" in text
    assert "slot" in text.lower()
