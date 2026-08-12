from copy import deepcopy

from django.contrib import admin

from mezzanine.core.admin import DisplayableAdmin
from mezzanine.music.models import Album, Artist, Playlist, PlaylistTrack, Track


class PlaylistTrackInline(admin.TabularInline):
    model = PlaylistTrack
    extra = 1
    autocomplete_fields = ("track",)
    ordering = ("sort_order",)


def _displayable_fieldsets(*extra_fields):
    fieldsets = deepcopy(DisplayableAdmin.fieldsets)
    fields = list(fieldsets[0][1]["fields"])
    fields.extend(extra_fields)
    fieldsets[0][1]["fields"] = fields
    return fieldsets


@admin.register(Artist)
class ArtistAdmin(DisplayableAdmin):
    fieldsets = _displayable_fieldsets("bio", "cover_key", "monthly_listeners")
    list_display = ("title", "status", "monthly_listeners", "admin_link")
    search_fields = ("title", "bio")


@admin.register(Album)
class AlbumAdmin(DisplayableAdmin):
    fieldsets = _displayable_fieldsets("artist", "year", "album_type", "cover_key")
    list_display = ("title", "artist", "year", "status", "admin_link")
    list_filter = DisplayableAdmin.list_filter + ("artist",)
    search_fields = ("title", "artist__title")
    autocomplete_fields = ("artist",)


@admin.register(Track)
class TrackAdmin(DisplayableAdmin):
    fieldsets = _displayable_fieldsets("artist", "album", "duration", "explicit")
    list_display = ("title", "artist", "album", "duration", "status", "admin_link")
    list_filter = DisplayableAdmin.list_filter + ("artist", "explicit")
    search_fields = ("title", "artist__title", "album__title")
    autocomplete_fields = ("artist", "album")


@admin.register(Playlist)
class PlaylistAdmin(DisplayableAdmin):
    fieldsets = _displayable_fieldsets("owner_label", "cover_key", "featured")
    list_display = ("title", "featured", "owner_label", "status", "admin_link")
    list_filter = DisplayableAdmin.list_filter + ("featured",)
    search_fields = ("title", "description")
    inlines = (PlaylistTrackInline,)
