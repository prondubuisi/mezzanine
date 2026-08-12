"""Public URL routes for the music plugin (CPT archives / singles)."""

from django.urls import path

from mezzanine.music import views

urlpatterns = [
    path("", views.home, name="home"),
    path("search/", views.search, name="music_search"),
    path("library/", views.library, name="music_library"),
    path("playlist/<slug:slug>/", views.playlist_detail, name="music_playlist"),
    path("album/<slug:slug>/", views.album_detail, name="music_album"),
    path("artist/<slug:slug>/", views.artist_detail, name="music_artist"),
]
