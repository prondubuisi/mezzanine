"""Spotify listening theme + music CMS plugin (WordPress theme/plugin split)."""

import sys
import types
from pathlib import Path

import pytest
from django.core.management import call_command
from django.test import Client
from django.urls import clear_url_caches, include, path, set_urlconf

import mezzanine
from mezzanine.kits.loader import (
    apply_kit,
    kit_plugins,
    kit_seed_command,
    kit_urlconf,
    kit_wants_blog,
    load_kit_meta,
    validate_kit,
)

REPO = Path(mezzanine.__file__).resolve().parent.parent


def test_spotify_kit_is_theme_not_data_owner():
    root, meta = load_kit_meta("spotify")
    assert meta["name"] == "spotify"
    assert kit_wants_blog(meta) is False
    assert "mezzanine.music" in kit_plugins(meta)
    assert kit_urlconf(meta) == "mezzanine.music.urls"
    assert kit_seed_command(meta) == "seed_music_demo"
    validate_kit(meta)
    # Theme assets only — no kit views/urls.
    assert not (root / "views.py").exists()
    assert not (root / "urls.py").exists()
    assert (root / "templates/music/home.html").is_file()
    assert (root / "static/spotify/player.css").is_file()
    assert "music.Track" in meta["types"]


def test_apply_spotify_installs_music_plugin(tmp_path):
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
    (project / app / "urls.py").write_text(
        "from django.urls import include, path\n"
        "from django.views.generic import TemplateView\n"
        "urlpatterns = [\n"
        '    path("", TemplateView.as_view(template_name="index.html"), name="home"),\n'
        '    path("", include("mezzanine.urls")),\n'
        "]\n",
        encoding="utf-8",
    )
    apply_kit("spotify", project, app)
    settings = (project / app / "settings.py").read_text(encoding="utf-8")
    assert "mezzanine.kits.spotify" in settings
    assert "mezzanine.music" in settings
    assert "mezzanine.blog" not in settings
    urls = (project / app / "urls.py").read_text(encoding="utf-8")
    assert "mezzanine.music.urls" in urls
    assert (project / "templates/music/home.html").is_file()


@pytest.fixture
def music_client(settings):
    apps = list(settings.INSTALLED_APPS)
    if "mezzanine.music" not in apps:
        apps.append("mezzanine.music")
    if "mezzanine.kits.spotify" not in apps:
        apps.append("mezzanine.kits.spotify")
    settings.INSTALLED_APPS = apps
    # Ensure music migrations can run — pytest uses project apps; migrate music.
    call_command("migrate", "music", verbosity=0, interactive=False)
    mod = types.ModuleType("nova_test_music_urls")
    mod.urlpatterns = [path("", include("mezzanine.music.urls"))]
    sys.modules["nova_test_music_urls"] = mod
    settings.ROOT_URLCONF = "nova_test_music_urls"
    clear_url_caches()
    set_urlconf(settings.ROOT_URLCONF)
    yield Client()
    set_urlconf(None)
    clear_url_caches()
    sys.modules.pop("nova_test_music_urls", None)


@pytest.mark.django_db
def test_music_cms_seed_and_public_flow(music_client):
    call_command("seed_music_demo", flush=True, verbosity=0)
    from mezzanine.music.models import Artist, Playlist, Track

    assert Artist.objects.filter(status=2).count() >= 1
    assert Track.objects.count() >= 8
    assert Playlist.objects.filter(featured=True).exists()

    client = music_client
    for path in (
        "/",
        "/search/?q=Luna",
        "/library/",
        "/playlist/daily-mix-1/",
        "/album/night-bus/",
        "/artist/luna-park/",
    ):
        resp = client.get(path)
        assert resp.status_code == 200, path

    home = client.get("/").content.decode("utf-8")
    assert "Daily Mix 1" in home
    assert "sp-app" in home or "Playlists" in home
    assert "Newsroom" not in home
    # CMS disclaimer
    assert "CMS" in home or "content" in home.lower()

    # Admin-editable: rename playlist and see it on the site.
    pl = Playlist.objects.get(slug="daily-mix-1")
    pl.title = "Daily Mix CMS Edit"
    pl.save()
    home2 = client.get("/").content.decode("utf-8")
    assert "Daily Mix CMS Edit" in home2


def test_spotify_doc_describes_plugin_theme_split():
    text = (REPO / "docs/modernization/demo-clones/SPOTIFY.md").read_text(
        encoding="utf-8"
    )
    assert "mezzanine.music" in text
    assert "plugin" in text.lower()
    assert "theme" in text.lower()
    assert "seed_music_demo" in text
