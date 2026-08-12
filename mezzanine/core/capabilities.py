"""Narrow Y1 capability helper.

Used by ``/edit/`` and preview-token issue. Django admin keeps model
perms plus ``has_site_permission`` (a ``SiteRole`` row for the current
site, or superuser).
"""

from mezzanine.core.models import (
    ROLE_ADMIN,
    ROLE_AUTHOR,
    ROLE_EDITOR,
    ROLE_PUBLISHER,
    SiteRole,
)
from mezzanine.utils.deprecation import is_authenticated
from mezzanine.utils.sites import current_site_id

CAP_PAGE_EDIT_OWN = "page.edit_own"
CAP_PAGE_EDIT = "page.edit"
CAP_PAGE_MOVE = "page.move"
CAP_BLOG_EDIT_OWN = "blog.edit_own"
CAP_BLOG_EDIT = "blog.edit"
CAP_PREVIEW_ISSUE = "preview.issue"

# author ⊂ editor ⊂ publisher ⊂ admin
_ROLE_CAPS = {
    ROLE_AUTHOR: frozenset({CAP_PAGE_EDIT_OWN, CAP_BLOG_EDIT_OWN}),
    ROLE_EDITOR: frozenset(
        {
            CAP_PAGE_EDIT_OWN,
            CAP_BLOG_EDIT_OWN,
            CAP_PAGE_EDIT,
            CAP_BLOG_EDIT,
            CAP_PAGE_MOVE,
        }
    ),
    ROLE_PUBLISHER: frozenset(
        {
            CAP_PAGE_EDIT_OWN,
            CAP_BLOG_EDIT_OWN,
            CAP_PAGE_EDIT,
            CAP_BLOG_EDIT,
            CAP_PAGE_MOVE,
            CAP_PREVIEW_ISSUE,
        }
    ),
    ROLE_ADMIN: frozenset(
        {
            CAP_PAGE_EDIT_OWN,
            CAP_BLOG_EDIT_OWN,
            CAP_PAGE_EDIT,
            CAP_BLOG_EDIT,
            CAP_PAGE_MOVE,
            CAP_PREVIEW_ISSUE,
        }
    ),
}


def role_for_user(user, site_id=None):
    """Return the ``SiteRole.role`` string, or ``None``.

    Memoized per request when a request is bound (DESIGN.md Amendment 2 N1 /
    PR-039). Cache key is ``(user_id, site_id)`` on the request, matching the
    shape of ``SitePermissionMiddleware``'s ``has_site_permission`` cache.
    """
    if user is None or not is_authenticated(user):
        return None
    if site_id is None:
        site_id = current_site_id()

    request = None
    try:
        from mezzanine.core.request import current_request

        request = current_request()
    except Exception:  # noqa: BLE001 — never fail capability checks
        request = None

    cache_key = (getattr(user, "pk", None), site_id)
    if request is not None:
        cache = getattr(request, "_nova_role_cache", None)
        if cache is None:
            cache = {}
            request._nova_role_cache = cache
        if cache_key in cache:
            return cache[cache_key]

    try:
        role = SiteRole.objects.get(user=user, site_id=site_id).role
    except SiteRole.DoesNotExist:
        role = None

    if request is not None:
        request._nova_role_cache[cache_key] = role
    return role


def user_has_capability(user, capability, *, site_id=None, obj=None):
    """True when ``user`` has ``capability`` on ``site_id`` (or ``obj.site``).

    Superuser: all sites, all capabilities. ``*.edit_own`` also requires
    ``obj.user_id == user.id`` when ``obj`` is given.
    """
    if user is None or not is_authenticated(user) or not user.is_active:
        return False
    if user.is_superuser:
        return True
    if site_id is None:
        site_id = getattr(obj, "site_id", None) or current_site_id()
    role = role_for_user(user, site_id=site_id)
    if role is None or capability not in _ROLE_CAPS.get(role, ()):
        return False
    if capability.endswith(".edit_own") and obj is not None:
        return getattr(obj, "user_id", None) == user.id
    return True


def user_can_edit(user, obj):
    """``page.edit`` / ``blog.edit``, or the matching ``*_own`` capability."""
    app = obj._meta.app_label
    if app == "blog":
        return user_has_capability(
            user, CAP_BLOG_EDIT, obj=obj
        ) or user_has_capability(user, CAP_BLOG_EDIT_OWN, obj=obj)
    return user_has_capability(user, CAP_PAGE_EDIT, obj=obj) or user_has_capability(
        user, CAP_PAGE_EDIT_OWN, obj=obj
    )


def user_can_issue_preview(user, obj=None, site_id=None):
    return user_has_capability(
        user, CAP_PREVIEW_ISSUE, site_id=site_id, obj=obj
    )
