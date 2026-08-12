"""
Public views over CMS music content (plugin).

Templates live in the active kit/theme (``music/*.html``); this module
only loads published model data — WordPress-style “query in template hierarchy”.
"""

from __future__ import annotations

from django.db.models import Q
from django.shortcuts import get_object_or_404, render

from mezzanine.kits.theme import resolve_slot_template
from mezzanine.music.models import Album, Artist, Playlist, Track


def _tpl(slot: str, fallback: str) -> str:
    """Resolve theme.json slot → template path (WP hierarchy step)."""
    return resolve_slot_template(slot, fallback)


def _preview(request):
    return getattr(request, "preview", None)


def _shell(request, extra=None):
    preview = _preview(request)
    playlists = list(
        Playlist.objects.published(for_user=request.user, preview=preview).order_by(
            "title"
        )[:8]
    )
    now = (
        Track.objects.published(for_user=request.user, preview=preview)
        .select_related("artist", "album")
        .first()
    )
    ctx = {
        "site_name": "Nova Listen",
        "library_playlists": playlists,
        "now_playing": now,
        "disclaimer": (
            "CMS demo: artists, albums, tracks, and playlists are Nova content "
            "types (plugin). This kit is presentation only. Not affiliated with Spotify."
        ),
    }
    if extra:
        ctx.update(extra)
    return ctx


def home(request):
    preview = _preview(request)
    pub = dict(for_user=request.user, preview=preview)
    playlists = list(
        Playlist.objects.published(**pub).filter(featured=True).order_by("title")
    )
    if not playlists:
        playlists = list(Playlist.objects.published(**pub).order_by("title")[:5])
    albums = list(
        Album.objects.published(**pub)
        .select_related("artist")
        .order_by("-year", "title")[:8]
    )
    recent = list(
        Track.objects.published(**pub)
        .select_related("artist", "album")
        .order_by("-publish_date")[:4]
    )
    return render(
        request,
        _tpl("home", "music/home.html"),
        _shell(
            request,
            {
                "page": "home",
                "greeting": "Good evening",
                "playlists": playlists,
                "albums": albums,
                "recent": recent,
            },
        ),
    )


def search(request):
    q = (request.GET.get("q") or "").strip()
    preview = _preview(request)
    pub = dict(for_user=request.user, preview=preview)
    results = {"tracks": [], "artists": [], "albums": [], "playlists": []}
    if q:
        results["tracks"] = list(
            Track.objects.published(**pub)
            .filter(
                Q(title__icontains=q)
                | Q(artist__title__icontains=q)
                | Q(album__title__icontains=q)
            )
            .select_related("artist", "album")[:20]
        )
        results["artists"] = list(
            Artist.objects.published(**pub).filter(title__icontains=q)[:10]
        )
        results["albums"] = list(
            Album.objects.published(**pub)
            .filter(Q(title__icontains=q) | Q(artist__title__icontains=q))
            .select_related("artist")[:10]
        )
        results["playlists"] = list(
            Playlist.objects.published(**pub).filter(
                Q(title__icontains=q) | Q(description__icontains=q)
            )[:10]
        )  # description is Displayable.description
    return render(
        request,
        _tpl("search", "music/search.html"),
        _shell(request, {"page": "search", "q": q, "results": results}),
    )


def library(request):
    preview = _preview(request)
    pub = dict(for_user=request.user, preview=preview)
    return render(
        request,
        _tpl("library", "music/library.html"),
        _shell(
            request,
            {
                "page": "library",
                "playlists": list(Playlist.objects.published(**pub).order_by("title")),
                "artists": list(Artist.objects.published(**pub).order_by("title")[:12]),
                "albums": list(
                    Album.objects.published(**pub)
                    .select_related("artist")
                    .order_by("-year")[:12]
                ),
            },
        ),
    )


def playlist_detail(request, slug):
    preview = _preview(request)
    pl = get_object_or_404(
        Playlist.objects.published(for_user=request.user, preview=preview),
        slug=slug,
    )
    tracks = pl.ordered_tracks()
    # Only published tracks
    tracks = [t for t in tracks if t.published() or preview]
    now = tracks[0] if tracks else None
    return render(
        request,
        _tpl("playlist", "music/playlist.html"),
        _shell(
            request,
            {
                "page": "playlist",
                "playlist": pl,
                "tracks": tracks,
                "now_playing": now or _shell(request)["now_playing"],
            },
        ),
    )


def album_detail(request, slug):
    preview = _preview(request)
    album = get_object_or_404(
        Album.objects.published(for_user=request.user, preview=preview).select_related(
            "artist"
        ),
        slug=slug,
    )
    tracks = list(
        album.tracks.published(for_user=request.user, preview=preview).select_related(
            "artist", "album"
        )
    )
    now = tracks[0] if tracks else None
    return render(
        request,
        _tpl("album", "music/album.html"),
        _shell(
            request,
            {
                "page": "album",
                "album": album,
                "tracks": tracks,
                "now_playing": now or _shell(request)["now_playing"],
            },
        ),
    )


def artist_detail(request, slug):
    preview = _preview(request)
    artist = get_object_or_404(
        Artist.objects.published(for_user=request.user, preview=preview),
        slug=slug,
    )
    tracks = list(
        artist.tracks.published(for_user=request.user, preview=preview).select_related(
            "artist", "album"
        )[:20]
    )
    albums = list(
        artist.albums.published(for_user=request.user, preview=preview).order_by(
            "-year"
        )
    )
    now = tracks[0] if tracks else None
    return render(
        request,
        _tpl("artist", "music/artist.html"),
        _shell(
            request,
            {
                "page": "artist",
                "artist": artist,
                "tracks": tracks,
                "albums": albums,
                "now_playing": now or _shell(request)["now_playing"],
            },
        ),
    )
