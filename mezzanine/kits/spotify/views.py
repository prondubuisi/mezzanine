"""Spotify Web Player–style demo views (catalog data, not CMS pages)."""

from __future__ import annotations

from django.http import Http404
from django.shortcuts import render

from mezzanine.demos import music_catalog as catalog


def _shell(extra: dict | None = None) -> dict:
    ctx = {
        "site_name": "Nova Listen",
        "now_playing": catalog.default_now_playing(),
        "library_playlists": [
            catalog.PLAYLISTS[i] for i in catalog.LIBRARY_PLAYLIST_IDS[:5]
        ],
        "disclaimer": (
            "Unofficial UI demo inspired by the Spotify web player. "
            "Not affiliated with Spotify AB. No real audio streaming."
        ),
    }
    if extra:
        ctx.update(extra)
    return ctx


def home(request):
    return render(
        request,
        "spotify/home.html",
        _shell({"page": "home", **catalog.home_context()}),
    )


def search(request):
    q = request.GET.get("q", "")
    results = catalog.search(q)
    return render(
        request,
        "spotify/search.html",
        _shell({"page": "search", "q": q, "results": results}),
    )


def library(request):
    return render(
        request,
        "spotify/library.html",
        _shell({"page": "library", **catalog.library_context()}),
    )


def playlist_detail(request, slug):
    pl = catalog.get_playlist(slug)
    if pl is None:
        raise Http404
    return render(
        request,
        "spotify/playlist.html",
        _shell({"page": "playlist", "playlist": pl, "now_playing": pl["tracks"][0] if pl["tracks"] else catalog.default_now_playing()}),
    )


def album_detail(request, slug):
    al = catalog.get_album(slug)
    if al is None:
        raise Http404
    return render(
        request,
        "spotify/album.html",
        _shell({"page": "album", "album": al, "now_playing": al["tracks"][0] if al["tracks"] else catalog.default_now_playing()}),
    )


def artist_detail(request, slug):
    ar = catalog.get_artist(slug)
    if ar is None:
        raise Http404
    return render(
        request,
        "spotify/artist.html",
        _shell({"page": "artist", "artist": ar, "now_playing": ar["tracks"][0] if ar["tracks"] else catalog.default_now_playing()}),
    )
