"""
Seed CMS music content (plugin data), not theme chrome.

Usage::

    python manage.py seed_music_demo
    python manage.py seed_music_demo --flush
"""

from __future__ import annotations

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from mezzanine.core.models import CONTENT_STATUS_PUBLISHED
from mezzanine.demos import music_catalog as catalog


class Command(BaseCommand):
    help = "Seed Artist/Album/Track/Playlist CMS objects for the music plugin."

    def add_arguments(self, parser):
        parser.add_argument(
            "--flush",
            action="store_true",
            help="Delete existing music catalog objects first.",
        )

    def handle(self, *args, **options):
        try:
            from mezzanine.music.models import (
                Album,
                Artist,
                Playlist,
                PlaylistTrack,
                Track,
            )
        except Exception as exc:  # noqa: BLE001
            raise CommandError(
                "mezzanine.music is not installed (add to INSTALLED_APPS)."
            ) from exc

        if options["flush"]:
            self.stdout.write("Flushing music catalog…")
            PlaylistTrack.objects.all().delete()
            Playlist.objects.all().delete()
            Track.objects.all().delete()
            Album.objects.all().delete()
            Artist.objects.all().delete()

        now = timezone.now()
        artists = {}
        for slug, data in catalog.ARTISTS.items():
            obj, _ = Artist.objects.update_or_create(
                slug=slug,
                defaults={
                    "title": data["name"],
                    "bio": data.get("bio", ""),
                    "cover_key": data.get("cover", "violet"),
                    "monthly_listeners": data.get("monthly_listeners", ""),
                    "status": CONTENT_STATUS_PUBLISHED,
                    "publish_date": now,
                },
            )
            artists[slug] = obj
            self.stdout.write(f"  artist: {slug}")

        albums = {}
        for slug, data in catalog.ALBUMS.items():
            obj, _ = Album.objects.update_or_create(
                slug=slug,
                defaults={
                    "title": data["title"],
                    "artist": artists[data["artist_id"]],
                    "year": data.get("year"),
                    "cover_key": data.get("cover", "ocean"),
                    "album_type": data.get("type", "Album"),
                    "status": CONTENT_STATUS_PUBLISHED,
                    "publish_date": now,
                },
            )
            albums[slug] = obj
            self.stdout.write(f"  album: {slug}")

        tracks = {}
        for slug, data in catalog.TRACKS.items():
            obj, _ = Track.objects.update_or_create(
                slug=slug,
                defaults={
                    "title": data["title"],
                    "artist": artists[data["artist_id"]],
                    "album": albums.get(data.get("album_id")),
                    "duration": data.get("duration", "0:00"),
                    "explicit": bool(data.get("explicit")),
                    "status": CONTENT_STATUS_PUBLISHED,
                    "publish_date": now,
                },
            )
            tracks[slug] = obj
            self.stdout.write(f"  track: {slug}")

        featured_ids = set(catalog.HOME_FEATURED_PLAYLISTS)
        for slug, data in catalog.PLAYLISTS.items():
            pl, _ = Playlist.objects.update_or_create(
                slug=slug,
                defaults={
                    "title": data["title"],
                    "description": data.get("description", ""),
                    "gen_description": False,
                    "owner_label": data.get("owner", "Nova"),
                    "cover_key": data.get("cover", "mint"),
                    "featured": slug in featured_ids,
                    "status": CONTENT_STATUS_PUBLISHED,
                    "publish_date": now,
                },
            )
            PlaylistTrack.objects.filter(playlist=pl).delete()
            for order, tid in enumerate(data.get("track_ids", [])):
                if tid not in tracks:
                    continue
                PlaylistTrack.objects.create(
                    playlist=pl, track=tracks[tid], sort_order=order
                )
            self.stdout.write(f"  playlist: {slug}")

        self.stdout.write(self.style.SUCCESS("Music CMS catalog seeded."))
        self.stdout.write(
            "Edit content in Admin → Music. Theme kit only changes appearance."
        )
