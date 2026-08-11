from django.core.checks import Error, Warning, register
from django.db.utils import OperationalError, ProgrammingError

from mezzanine.conf import settings
from mezzanine.core.defaults import (
    RICHTEXT_FILTER_LEVEL_HIGH,
    RICHTEXT_FILTER_LEVEL_NONE,
    nova_force_raw_html,
)
from mezzanine.utils.conf import middlewares_or_subclasses_installed
from mezzanine.utils.sites import SITE_PERMISSION_MIDDLEWARE

LOADER_TAGS_WARNING = (
    "You have included 'mezzanine.template.loader_tags' as a builtin in your template "
    "configuration. 'loader_tags' no longer exists and should be removed. If you're "
    "still using the {% overextends %} tag please replace it with Django's "
    "{% extend %} for identical results."
)

RICHTEXT_FILTER_LEVEL_NONE_WARNING = (
    "HTML sanitization is disabled (RICHTEXT_FILTER_LEVEL=NONE or "
    "NOVA_FORCE_RAW_HTML=1). This allows staff to persist script tags. "
    "RICHTEXT_FILTER_LEVEL is not admin-editable. NONE is only honored "
    "when NOVA_FORCE_RAW_HTML=1."
)

EXTRA_MODEL_FIELDS_WARNING = (
    "EXTRA_MODEL_FIELDS is set. Injecting fields at import time is deprecated "
    "and will become an error. Prefer a real model field or a sidecar model."
)

NEVERCACHE_KEY_EMPTY_WARNING = (
    "NEVERCACHE_KEY is empty. Generate a unique 50-character value "
    "(nova-project / mezzanine-project does this automatically)."
)

NEVERCACHE_KEY_EMPTY_ERROR = (
    "NEVERCACHE_KEY is empty but Mezzanine cache middleware is installed. "
    "An empty key makes nevercache delimiters guessable. Set a unique "
    "50-character NEVERCACHE_KEY."
)

CACHE_MIDDLEWARES = (
    "mezzanine.core.middleware.UpdateCacheMiddleware",
    "mezzanine.core.middleware.FetchFromCacheMiddleware",
)


@register()
def check_template_settings(app_configs, **kwargs):
    issues = []

    if any(
        "mezzanine.template.loader_tags"
        in config.get("OPTIONS", {}).get("builtins", {})
        for config in settings.TEMPLATES
    ):
        issues.append(Warning(LOADER_TAGS_WARNING, id="mezzanine.core.W05"))

    return issues


@register()
def check_sites_middleware(app_configs, **kwargs):

    if not middlewares_or_subclasses_installed([SITE_PERMISSION_MIDDLEWARE]):
        return [
            Warning(
                f"{SITE_PERMISSION_MIDDLEWARE} missing from settings.MIDDLEWARE - "
                "per site permissions not applied",
                id="mezzanine.core.W04",
            )
        ]
    return []


@register()
def check_richtext_filter_level_none(app_configs, **kwargs):
    """Warn if raw HTML is enabled via NONE or NOVA_FORCE_RAW_HTML=1.

    The setting is not admin-editable. A leftover database row is
    ignored; settings.py NONE still warns so operators clean it up.
    """
    try:
        level = settings.RICHTEXT_FILTER_LEVEL
    except (OperationalError, ProgrammingError):
        # Setting table may not exist yet (e.g. ``manage.py check`` before
        # migrate). Fall back to Django settings / the registered default.
        from django.conf import settings as django_settings

        level = getattr(
            django_settings, "RICHTEXT_FILTER_LEVEL", RICHTEXT_FILTER_LEVEL_HIGH
        )

    if level == RICHTEXT_FILTER_LEVEL_NONE or nova_force_raw_html():
        return [
            Warning(
                RICHTEXT_FILTER_LEVEL_NONE_WARNING,
                id="mezzanine.core.W06",
            )
        ]
    return []


@register()
def check_extra_model_fields(app_configs, **kwargs):
    """Warn when EXTRA_MODEL_FIELDS injects schema at import time."""
    extra = getattr(settings, "EXTRA_MODEL_FIELDS", ()) or ()
    if extra:
        return [
            Warning(
                EXTRA_MODEL_FIELDS_WARNING,
                id="mezzanine.core.W07",
            )
        ]
    return []


@register()
def check_nevercache_key(app_configs, **kwargs):
    """Refuse an empty NEVERCACHE_KEY when cache middleware is on."""
    key = getattr(settings, "NEVERCACHE_KEY", "") or ""
    if str(key).strip():
        return []
    middleware = getattr(settings, "MIDDLEWARE", ()) or ()
    if any(name in middleware for name in CACHE_MIDDLEWARES):
        return [
            Error(
                NEVERCACHE_KEY_EMPTY_ERROR,
                id="mezzanine.core.E01",
            )
        ]
    return [
        Warning(
            NEVERCACHE_KEY_EMPTY_WARNING,
            id="mezzanine.core.W08",
        )
    ]
