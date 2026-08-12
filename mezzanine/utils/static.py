"""
Utils for working with static files.
"""
from django.conf import settings
from django.templatetags.static import static


def static_lazy(path):
    """
    Resolve a static asset path for form/admin ``Media`` definitions.

    Historically this returned ``lazy(static, str)(path)`` for cache-busting
    when ``STATIC_URL`` was not ready at import. Django 6's ``Media`` converts
    plain ``str`` paths to ``Script``/``Stylesheet`` assets that call
    ``static()`` at render time; a lazy ``__proxy__`` is not a ``str`` and has
    no ``__html__``, so ``Media.render_js`` raises.

    Pass relative paths through so ``Script.path`` can resolve them. Absolute
    or scheme-qualified URLs are returned unchanged.
    """
    if isinstance(path, str) and path.startswith(("http://", "https://", "/")):
        return path
    storage = getattr(settings, "STATICFILES_STORAGE", "") or ""
    # Manifest storage already rewrites relative Media paths; keep them plain.
    if str(storage).endswith("ManifestStaticFilesStorage"):
        return path
    # Non-manifest: resolve eagerly so callers that expect a full URL still work
    # outside Media (templates rarely use this helper).
    try:
        return static(path)
    except Exception:
        return path
