"""URL routes for the Spotify Web Player–style demo kit."""

from django.urls import path

from mezzanine.kits.spotify import views

# Un-namespaced ``home`` — Mezzanine pages middleware calls reverse("home").
urlpatterns = [
    path("", views.home, name="home"),
    path("search/", views.search, name="spotify_search"),
    path("library/", views.library, name="spotify_library"),
    path("playlist/<slug:slug>/", views.playlist_detail, name="spotify_playlist"),
    path("album/<slug:slug>/", views.album_detail, name="spotify_album"),
    path("artist/<slug:slug>/", views.artist_detail, name="spotify_artist"),
]
