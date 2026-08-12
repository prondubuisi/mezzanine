"""
Seed *source* for the music CMS plugin (not runtime catalog).

``seed_music_demo`` writes these dicts into ``mezzanine.music`` models.
Themes never import this module at request time — WordPress analogue:
import JSON / demo content, not hard-coded theme data.

Original demo titles (not licensed catalog or trademarks).
"""

from __future__ import annotations

from typing import Any

# Accent colors for placeholder cover art (CSS gradients).
COVERS = {
    "ember": ("#ff6b35", "#1a1a2e"),
    "ocean": ("#00d4ff", "#0b132b"),
    "violet": ("#b5179e", "#240046"),
    "forest": ("#2d6a4f", "#081c15"),
    "gold": ("#f4a261", "#1d3557"),
    "rose": ("#e63946", "#1d1d1d"),
    "mint": ("#06d6a0", "#073b4c"),
    "sky": ("#4cc9f0", "#3a0ca3"),
}


def _track(
    id_: str,
    title: str,
    artist_id: str,
    album_id: str,
    duration: str,
    explicit: bool = False,
) -> dict[str, Any]:
    return {
        "id": id_,
        "title": title,
        "artist_id": artist_id,
        "album_id": album_id,
        "duration": duration,
        "explicit": explicit,
    }


ARTISTS: dict[str, dict[str, Any]] = {
    "luna-park": {
        "id": "luna-park",
        "name": "Luna Park",
        "bio": "Indie electronic duo from Lisbon.",
        "cover": "violet",
        "monthly_listeners": "2.4M",
    },
    "cedar-line": {
        "id": "cedar-line",
        "name": "Cedar Line",
        "bio": "Folk-rock storytellers.",
        "cover": "forest",
        "monthly_listeners": "890K",
    },
    "neon-harbor": {
        "id": "neon-harbor",
        "name": "Neon Harbor",
        "bio": "Late-night synth pop.",
        "cover": "ocean",
        "monthly_listeners": "1.1M",
    },
    "maris-cole": {
        "id": "maris-cole",
        "name": "Maris Cole",
        "bio": "R&B songwriter.",
        "cover": "rose",
        "monthly_listeners": "3.2M",
    },
    "atlas-wave": {
        "id": "atlas-wave",
        "name": "Atlas Wave",
        "bio": "Ambient and focus scores.",
        "cover": "sky",
        "monthly_listeners": "5.0M",
    },
}

ALBUMS: dict[str, dict[str, Any]] = {
    "night-bus": {
        "id": "night-bus",
        "title": "Night Bus",
        "artist_id": "luna-park",
        "year": 2024,
        "cover": "violet",
        "type": "Album",
    },
    "porch-light": {
        "id": "porch-light",
        "title": "Porch Light",
        "artist_id": "cedar-line",
        "year": 2023,
        "cover": "forest",
        "type": "Album",
    },
    "glass-hours": {
        "id": "glass-hours",
        "title": "Glass Hours",
        "artist_id": "neon-harbor",
        "year": 2025,
        "cover": "ocean",
        "type": "Album",
    },
    "soft-signal": {
        "id": "soft-signal",
        "title": "Soft Signal",
        "artist_id": "maris-cole",
        "year": 2024,
        "cover": "rose",
        "type": "Album",
    },
    "deep-work": {
        "id": "deep-work",
        "title": "Deep Work",
        "artist_id": "atlas-wave",
        "year": 2022,
        "cover": "sky",
        "type": "Album",
    },
}

TRACKS: dict[str, dict[str, Any]] = {
    t["id"]: t
    for t in [
        _track("nb-01", "Ticket Stub", "luna-park", "night-bus", "3:12"),
        _track("nb-02", "Fluorescent Heart", "luna-park", "night-bus", "2:58"),
        _track("nb-03", "Last Stop Before Dawn", "luna-park", "night-bus", "4:05"),
        _track("nb-04", "Metro Ghosts", "luna-park", "night-bus", "3:41"),
        _track("pl-01", "Red Door", "cedar-line", "porch-light", "3:33"),
        _track("pl-02", "County Line", "cedar-line", "porch-light", "4:18"),
        _track("pl-03", "Two Chairs", "cedar-line", "porch-light", "3:02"),
        _track("gh-01", "Afterglow Protocol", "neon-harbor", "glass-hours", "3:27"),
        _track("gh-02", "Static Kiss", "neon-harbor", "glass-hours", "2:49", True),
        _track("gh-03", "Pier 19", "neon-harbor", "glass-hours", "3:55"),
        _track("ss-01", "Leave the Light", "maris-cole", "soft-signal", "3:20"),
        _track("ss-02", "Slow Reply", "maris-cole", "soft-signal", "2:44"),
        _track("ss-03", "Gold Thread", "maris-cole", "soft-signal", "3:38"),
        _track("dw-01", "Focus Drift", "atlas-wave", "deep-work", "5:12"),
        _track("dw-02", "Quiet Circuit", "atlas-wave", "deep-work", "4:40"),
        _track("dw-03", "Blue Room Hum", "atlas-wave", "deep-work", "6:01"),
    ]
}

PLAYLISTS: dict[str, dict[str, Any]] = {
    "daily-mix-1": {
        "id": "daily-mix-1",
        "title": "Daily Mix 1",
        "description": "Luna Park, Neon Harbor, and more",
        "cover": "ember",
        "owner": "Nova",
        "track_ids": ["nb-01", "gh-01", "nb-02", "gh-03", "nb-03"],
    },
    "chill-hits": {
        "id": "chill-hits",
        "title": "Chill Hits",
        "description": "Kick back to the best new and soft tracks",
        "cover": "mint",
        "owner": "Nova",
        "track_ids": ["ss-01", "dw-01", "pl-03", "ss-02", "dw-02", "nb-04"],
    },
    "focus-flow": {
        "id": "focus-flow",
        "title": "Focus Flow",
        "description": "Instrumental energy for deep work",
        "cover": "sky",
        "owner": "Nova",
        "track_ids": ["dw-01", "dw-02", "dw-03", "nb-04"],
    },
    "evening-drive": {
        "id": "evening-drive",
        "title": "Evening Drive",
        "description": "Windows down, volume up",
        "cover": "gold",
        "owner": "Nova",
        "track_ids": ["gh-01", "pl-01", "ss-03", "gh-02", "pl-02", "nb-01"],
    },
    "liked-songs": {
        "id": "liked-songs",
        "title": "Liked Songs",
        "description": "Your saved tracks (demo)",
        "cover": "violet",
        "owner": "You",
        "track_ids": ["ss-01", "nb-02", "pl-01", "gh-01", "dw-01"],
    },
}

# Home shelf order.
HOME_FEATURED_PLAYLISTS = [
    "daily-mix-1",
    "chill-hits",
    "focus-flow",
    "evening-drive",
    "liked-songs",
]
HOME_FEATURED_ALBUMS = ["night-bus", "soft-signal", "glass-hours", "porch-light"]
LIBRARY_PLAYLIST_IDS = [
    "liked-songs",
    "daily-mix-1",
    "chill-hits",
    "focus-flow",
    "evening-drive",
]


def hydrate_track(track: dict[str, Any]) -> dict[str, Any]:
    out = dict(track)
    artist = ARTISTS[track["artist_id"]]
    album = ALBUMS[track["album_id"]]
    out["artist"] = artist
    out["album"] = album
    out["cover"] = album["cover"]
    return out


def playlist_tracks(playlist_id: str) -> list[dict[str, Any]]:
    pl = PLAYLISTS[playlist_id]
    return [hydrate_track(TRACKS[tid]) for tid in pl["track_ids"] if tid in TRACKS]


def album_tracks(album_id: str) -> list[dict[str, Any]]:
    rows = [t for t in TRACKS.values() if t["album_id"] == album_id]
    return [hydrate_track(t) for t in rows]


def artist_tracks(artist_id: str) -> list[dict[str, Any]]:
    rows = [t for t in TRACKS.values() if t["artist_id"] == artist_id]
    return [hydrate_track(t) for t in rows]


def search(query: str) -> dict[str, list[dict[str, Any]]]:
    q = (query or "").strip().lower()
    if not q:
        return {"tracks": [], "artists": [], "albums": [], "playlists": []}
    tracks = [
        hydrate_track(t)
        for t in TRACKS.values()
        if q in t["title"].lower()
        or q in ARTISTS[t["artist_id"]]["name"].lower()
        or q in ALBUMS[t["album_id"]]["title"].lower()
    ]
    artists = [a for a in ARTISTS.values() if q in a["name"].lower()]
    albums = [
        {**a, "artist": ARTISTS[a["artist_id"]]}
        for a in ALBUMS.values()
        if q in a["title"].lower()
        or q in ARTISTS[a["artist_id"]]["name"].lower()
    ]
    playlists = [p for p in PLAYLISTS.values() if q in p["title"].lower()]
    return {
        "tracks": tracks[:20],
        "artists": artists[:10],
        "albums": albums[:10],
        "playlists": playlists[:10],
    }


def get_playlist(slug: str) -> dict[str, Any] | None:
    pl = PLAYLISTS.get(slug)
    if not pl:
        return None
    return {**pl, "tracks": playlist_tracks(slug)}


def get_album(slug: str) -> dict[str, Any] | None:
    al = ALBUMS.get(slug)
    if not al:
        return None
    return {
        **al,
        "artist": ARTISTS[al["artist_id"]],
        "tracks": album_tracks(slug),
    }


def get_artist(slug: str) -> dict[str, Any] | None:
    ar = ARTISTS.get(slug)
    if not ar:
        return None
    albums = [
        {**a, "artist": ar}
        for a in ALBUMS.values()
        if a["artist_id"] == slug
    ]
    return {**ar, "albums": albums, "tracks": artist_tracks(slug)}


def home_context() -> dict[str, Any]:
    playlists = [PLAYLISTS[i] for i in HOME_FEATURED_PLAYLISTS]
    albums = [
        {**ALBUMS[i], "artist": ARTISTS[ALBUMS[i]["artist_id"]]}
        for i in HOME_FEATURED_ALBUMS
    ]
    greeting = "Good evening"
    return {
        "greeting": greeting,
        "playlists": playlists,
        "albums": albums,
        "recent": [
            hydrate_track(TRACKS[i])
            for i in ("ss-01", "nb-01", "gh-01", "pl-01")
        ],
    }


def library_context() -> dict[str, Any]:
    return {
        "playlists": [PLAYLISTS[i] for i in LIBRARY_PLAYLIST_IDS],
        "artists": list(ARTISTS.values())[:6],
        "albums": [
            {**a, "artist": ARTISTS[a["artist_id"]]} for a in list(ALBUMS.values())
        ],
    }


def default_now_playing() -> dict[str, Any]:
    return hydrate_track(TRACKS["nb-01"])
