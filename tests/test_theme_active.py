"""ACTIVE_THEME + theme.json contract (WordPress-style theme packages)."""

from pathlib import Path

import pytest
from django.test import Client, override_settings

import mezzanine
from mezzanine.kits.theme import (
    ThemeError,
    get_active_theme_name,
    list_theme_names,
    load_theme_meta,
    set_active_theme,
    theme_template_dir,
)

REPO = Path(mezzanine.__file__).resolve().parent.parent


def test_theme_json_packages_exist():
    names = list_theme_names()
    assert "whitehouse" in names
    assert "spotify" in names
    assert "magazine" in names
    for name in ("whitehouse", "spotify", "magazine"):
        meta = load_theme_meta(name)
        assert meta["name"] == name
        assert "version" in meta
        assert meta.get("slots") or meta.get("tokens")
        assert theme_template_dir(name)


def test_spotify_theme_declares_music_plugin():
    meta = load_theme_meta("spotify")
    assert "mezzanine.music" in (meta.get("plugins") or [])
    assert "home" in (meta.get("slots") or {})


def test_active_theme_loader_module_importable():
    from mezzanine.template.loaders.active_theme import Loader

    assert Loader is not None


@pytest.mark.django_db
def test_set_active_theme_persists_setting():
    from mezzanine.conf.models import Setting

    # whitehouse needs no extra plugins
    meta = set_active_theme("whitehouse")
    assert meta["name"] == "whitehouse"
    row = Setting.objects.filter(name="ACTIVE_THEME").first()
    assert row is not None
    assert row.value == "whitehouse"
    # Mezzanine settings may cache; get_active_theme reads conf after clear
    assert get_active_theme_name() in ("whitehouse", row.value)


@pytest.mark.django_db
def test_set_active_theme_spotify_requires_music_plugin():
    from django.conf import settings

    if "mezzanine.music" not in settings.INSTALLED_APPS:
        with pytest.raises(ThemeError, match="plugins"):
            set_active_theme("spotify")
    else:
        meta = set_active_theme("spotify")
        assert meta["name"] == "spotify"


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_demo_lab_lists_themes():
    client = Client()
    resp = client.get("/_nova/demo-sites/")
    assert resp.status_code == 200
    body = resp.content.decode("utf-8")
    assert "theme.json" in body or "Themes" in body
    assert "whitehouse" in body
    assert "spotify" in body
    assert "Activate theme" in body


def test_project_template_has_active_theme_loader():
    text = (
        REPO / "mezzanine/project_template/project_name/settings.py"
    ).read_text(encoding="utf-8")
    assert "active_theme.Loader" in text


def test_activate_theme_command_listed():
    from django.core.management import get_commands

    assert "activate_theme" in get_commands()


def test_theme_abstraction_doc_marks_theme_json_done():
    doc = REPO / "docs/modernization/demo-clones/THEME-ABSTRACTION.md"
    text = doc.read_text(encoding="utf-8")
    assert "theme.json" in text
    assert "ACTIVE_THEME" in text
