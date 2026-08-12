"""Spotify Web Player–style kit (music UI, not newsroom)."""

import sys
import types
from pathlib import Path

import pytest
from django.test import Client
from django.urls import clear_url_caches, include, path, set_urlconf

import mezzanine
from mezzanine.demos import music_catalog as catalog
from mezzanine.kits.loader import (
    apply_kit,
    kit_urlconf,
    kit_wants_blog,
    load_kit_meta,
    validate_kit,
)

REPO = Path(mezzanine.__file__).resolve().parent.parent
PLAYER_FLOW = (
    "/",
    "/search/",
    "/search/?q=Luna",
    "/library/",
    "/playlist/daily-mix-1/",
    "/album/night-bus/",
    "/artist/luna-park/",
)


def test_spotify_kit_is_player_not_newsroom():
    root, meta = load_kit_meta("spotify")
    assert meta["name"] == "spotify"
    assert kit_wants_blog(meta) is False
    assert kit_urlconf(meta) == "mezzanine.kits.spotify.urls"
    assert meta.get("seed_profile") in (None, "")
    validate_kit(meta)
    assert (root / "static/spotify/player.css").is_file()
    assert (root / "static/spotify/player.js").is_file()
    assert (root / "templates/spotify/home.html").is_file()
    assert (root / "templates/spotify/shell.html").is_file()
    # Old newsroom chrome must not ship in this kit.
    assert not (root / "templates/index.html").exists()
    assert not (root / "static/spotify/tokens.css").exists()


def test_music_catalog_search_and_hydrate():
    assert "luna-park" in catalog.ARTISTS
    hits = catalog.search("Luna")
    assert hits["artists"]
    assert any(t["title"] for t in hits["tracks"])
    pl = catalog.get_playlist("daily-mix-1")
    assert pl and pl["tracks"]
    assert pl["tracks"][0]["artist"]["name"]
    al = catalog.get_album("night-bus")
    assert al and al["artist"]["name"] == "Luna Park"
    ar = catalog.get_artist("luna-park")
    assert ar and ar["albums"]


def test_apply_spotify_kit_mounts_urlconf(tmp_path):
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
    assert "mezzanine.blog" not in settings
    urls = (project / app / "urls.py").read_text(encoding="utf-8")
    assert "mezzanine.kits.spotify.urls" in urls
    assert (project / "static/spotify/player.css").is_file()
    assert (project / "templates/spotify/home.html").is_file()
    assert (project / ".nova-kit").read_text().strip() == "spotify"


@pytest.fixture
def player_client(settings):
    """HTTP client with player urlconf + kit templates discoverable."""
    if "mezzanine.kits.spotify" not in settings.INSTALLED_APPS:
        settings.INSTALLED_APPS = list(settings.INSTALLED_APPS) + [
            "mezzanine.kits.spotify"
        ]
    mod = types.ModuleType("nova_test_spotify_urls")
    mod.urlpatterns = [
        path("", include("mezzanine.kits.spotify.urls")),
    ]
    sys.modules["nova_test_spotify_urls"] = mod
    settings.ROOT_URLCONF = "nova_test_spotify_urls"
    clear_url_caches()
    set_urlconf(settings.ROOT_URLCONF)
    yield Client()
    set_urlconf(None)
    clear_url_caches()
    sys.modules.pop("nova_test_spotify_urls", None)


@pytest.mark.django_db
def test_spotify_player_end_to_end_flow(player_client):
    client = player_client
    for path in PLAYER_FLOW:
        resp = client.get(path)
        assert resp.status_code == 200, path

    home = client.get("/").content.decode("utf-8")
    assert "sp-app" in home
    assert "Daily Mix 1" in home
    assert "Nova Listen" in home
    assert "newsroom" not in home.lower()
    assert "Company news" not in home

    search = client.get("/search/?q=Focus").content.decode("utf-8")
    assert "Focus Flow" in search or "Focus Drift" in search

    playlist = client.get("/playlist/daily-mix-1/").content.decode("utf-8")
    assert "Ticket Stub" in playlist or "Fluorescent" in playlist
    assert "sp-tracks" in playlist

    album = client.get("/album/night-bus/").content.decode("utf-8")
    assert "Night Bus" in album
    assert "Luna Park" in album

    artist = client.get("/artist/luna-park/").content.decode("utf-8")
    assert "Luna Park" in artist
    assert "monthly listeners" in artist.lower() or "2.4M" in artist

    library = client.get("/library/").content.decode("utf-8")
    assert "Your Library" in library
    assert "Liked Songs" in library

    missing = client.get("/playlist/not-a-real-list/")
    assert missing.status_code == 404


def test_demo_spotify_recipe_mentions_player():
    text = (REPO / "justfile").read_text(encoding="utf-8")
    assert "demo-spotify" in text
    assert "playlist/daily-mix-1" in text
    assert "Web Player" in text or "player" in text.lower()


def test_spotify_doc_is_player():
    doc = REPO / "docs/modernization/demo-clones/SPOTIFY.md"
    assert doc.is_file()
    text = doc.read_text(encoding="utf-8")
    assert "Web Player" in text or "music player" in text.lower()
    assert "not" in text.lower() and "newsroom" in text.lower()
