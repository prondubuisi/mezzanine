"""
CMS content types for a music / listening site (plugin layer).

Analogous to WordPress custom post types: Artist, Album, Track, Playlist.
Themes only render these; they do not own the data.
"""

from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from mezzanine.core.models import Displayable


class Artist(Displayable):
    """Performer / band (WP CPT: artist)."""

    bio = models.TextField(_("Biography"), blank=True)
    cover_key = models.CharField(
        _("Cover style"),
        max_length=32,
        default="violet",
        help_text=_("Demo cover token (gradient key), not a media file."),
    )
    monthly_listeners = models.CharField(
        _("Monthly listeners label"), max_length=64, blank=True
    )

    search_fields = {"title": 10, "bio": 5}

    class Meta:
        verbose_name = _("Artist")
        verbose_name_plural = _("Artists")
        ordering = ("title",)
        constraints = [
            models.UniqueConstraint(
                fields=["site", "slug"], name="music_artist_site_slug"
            ),
        ]

    def get_absolute_url(self):
        return reverse("music_artist", kwargs={"slug": self.slug})


class Album(Displayable):
    """Release (WP CPT: album)."""

    artist = models.ForeignKey(
        Artist,
        verbose_name=_("Artist"),
        related_name="albums",
        on_delete=models.CASCADE,
    )
    year = models.PositiveIntegerField(_("Year"), null=True, blank=True)
    cover_key = models.CharField(_("Cover style"), max_length=32, default="ocean")
    album_type = models.CharField(
        _("Type"), max_length=32, default="Album", help_text=_("Album, EP, Single…")
    )

    search_fields = {"title": 10}

    class Meta:
        verbose_name = _("Album")
        verbose_name_plural = _("Albums")
        ordering = ("-year", "title")
        constraints = [
            models.UniqueConstraint(
                fields=["site", "slug"], name="music_album_site_slug"
            ),
        ]

    def get_absolute_url(self):
        return reverse("music_album", kwargs={"slug": self.slug})


class Track(Displayable):
    """Song (WP CPT: track)."""

    artist = models.ForeignKey(
        Artist,
        verbose_name=_("Artist"),
        related_name="tracks",
        on_delete=models.CASCADE,
    )
    album = models.ForeignKey(
        Album,
        verbose_name=_("Album"),
        related_name="tracks",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    duration = models.CharField(_("Duration"), max_length=16, default="0:00")
    explicit = models.BooleanField(_("Explicit"), default=False)

    search_fields = {"title": 10}

    class Meta:
        verbose_name = _("Track")
        verbose_name_plural = _("Tracks")
        ordering = ("title",)
        constraints = [
            models.UniqueConstraint(
                fields=["site", "slug"], name="music_track_site_slug"
            ),
        ]

    def get_absolute_url(self):
        # Tracks play in-context; link to album or artist when present.
        if self.album_id:
            return self.album.get_absolute_url()
        return self.artist.get_absolute_url()

    @property
    def cover_key(self):
        if self.album_id:
            return self.album.cover_key
        return self.artist.cover_key


class Playlist(Displayable):
    """Curated list of tracks (WP CPT: playlist).

    Use Displayable.description for the public blurb (no second description field).
    """

    owner_label = models.CharField(
        _("Owner label"), max_length=64, default="Nova", blank=True
    )
    cover_key = models.CharField(_("Cover style"), max_length=32, default="mint")
    featured = models.BooleanField(
        _("Featured on home"),
        default=False,
        help_text=_("Show on the listening home shelf."),
    )
    tracks = models.ManyToManyField(
        Track,
        verbose_name=_("Tracks"),
        through="PlaylistTrack",
        related_name="playlists",
        blank=True,
    )

    search_fields = {"title": 10, "description": 5}

    class Meta:
        verbose_name = _("Playlist")
        verbose_name_plural = _("Playlists")
        ordering = ("title",)
        constraints = [
            models.UniqueConstraint(
                fields=["site", "slug"], name="music_playlist_site_slug"
            ),
        ]

    def get_absolute_url(self):
        return reverse("music_playlist", kwargs={"slug": self.slug})

    def ordered_tracks(self):
        return [
            pt.track
            for pt in self.playlist_tracks.select_related(
                "track", "track__artist", "track__album"
            )
        ]


class PlaylistTrack(models.Model):
    """Ordered membership (like a playlist meta box + order)."""

    playlist = models.ForeignKey(
        Playlist, related_name="playlist_tracks", on_delete=models.CASCADE
    )
    track = models.ForeignKey(
        Track, related_name="playlist_entries", on_delete=models.CASCADE
    )
    sort_order = models.PositiveIntegerField(_("Order"), default=0)

    class Meta:
        ordering = ("sort_order", "id")
        unique_together = (("playlist", "track"),)
        verbose_name = _("Playlist track")
        verbose_name_plural = _("Playlist tracks")


