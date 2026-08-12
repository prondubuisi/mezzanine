from django.contrib.auth import views as auth_views
from django.urls import path

from mezzanine.conf import settings
from mezzanine.core import views as core_views

urlpatterns = []

if "django.contrib.admin" in settings.INSTALLED_APPS:
    urlpatterns += [
        path(
            "password_reset/",
            auth_views.PasswordResetView.as_view(),
            name="password_reset",
        ),
        path(
            "password_reset/done/",
            auth_views.PasswordResetDoneView.as_view(),
            name="password_reset_done",
        ),
        path(
            "reset/done/",
            auth_views.PasswordResetCompleteView.as_view(),
            name="password_reset_complete",
        ),
        path(
            "reset/<uidb64>/<token>/",
            auth_views.PasswordResetConfirmView.as_view(),
            name="password_reset_confirm",
        ),
    ]

urlpatterns += [
    path("edit/", core_views.edit, name="edit"),
    path("search/", core_views.search, name="search"),
    path("set_site/", core_views.set_site, name="set_site"),
    # Y1.5 ops / media / private API (PR-036b, PR-026, PR-036)
    path("_nova/healthz", core_views.healthz, name="nova_healthz"),
    path("_nova/media/", core_views.media_list, name="nova_media_list"),
    path(
        "_nova/media/chooser/",
        core_views.media_chooser,
        name="nova_media_chooser",
    ),
    path(
        "_nova/media/<int:pk>/",
        core_views.media_detail,
        name="nova_media_detail",
    ),
    path(
        "_nova/media/<int:pk>/public/",
        core_views.media_public,
        name="nova_media_public",
    ),
    path("_nova/api/openapi.json", core_views.api_openapi, name="nova_api_openapi"),
    path("_nova/api/resolve", core_views.api_resolve, name="nova_api_resolve"),
    path("_nova/demo-sites/", core_views.demo_sites_index, name="nova_demo_sites"),
    path(
        "_nova/demo-sites/switch/",
        core_views.demo_sites_switch,
        name="nova_demo_sites_switch",
    ),
    path(
        "_nova/demo-sites/theme/",
        core_views.demo_theme_activate,
        name="nova_demo_theme_activate",
    ),
]
