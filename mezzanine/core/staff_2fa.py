"""
Optional staff TOTP (PR-023b / KD19).

Off by default. Enable with ``NOVA_STAFF_2FA=1`` (or settings
``NOVA_STAFF_2FA = True``) **and** install the ``otp`` extra
(``pip install 'nova-cms[otp]'`` → ``django-otp``).

Pytest / CI leave the flag off. Device enrollment must happen
before turning the flag on (create a TOTP device for the superuser
while 2FA is disabled, then set the env and restart).
"""

from __future__ import annotations

import os
from functools import lru_cache

from django.conf import settings

ENV_FLAG = "NOVA_STAFF_2FA"


def staff_2fa_setting_on() -> bool:
    """True when the operator requested staff 2FA (env or settings)."""
    env = os.environ.get(ENV_FLAG, "").strip().lower()
    if env in ("1", "true", "yes", "on"):
        return True
    if env in ("0", "false", "no", "off"):
        return False
    return bool(getattr(settings, "NOVA_STAFF_2FA", False))


@lru_cache(maxsize=1)
def django_otp_available() -> bool:
    try:
        import django_otp  # noqa: F401
    except ImportError:
        return False
    return True


def staff_2fa_enforced() -> bool:
    """
    True when staff must present a verified OTP for admin.

    Requires both the operator flag and an installed ``django-otp``.
    """
    if not staff_2fa_setting_on():
        return False
    return django_otp_available()


def user_otp_verified(request) -> bool:
    """
    Return True if the request user may pass the staff OTP gate.

    Uses ``request.user.is_verified()`` from django-otp's OTPMiddleware.
    Users with **no** registered devices are allowed through so an
    operator can enroll a TOTP device in admin after turning the flag
    on (enrollment grace). Once any device exists, verification is
    required.
    """
    user = getattr(request, "user", None)
    if user is None or not user.is_authenticated:
        return False
    if not (user.is_staff or user.is_superuser):
        return True
    is_verified = getattr(user, "is_verified", None)
    if callable(is_verified) and is_verified():
        return True
    try:
        from django_otp import user_has_device

        has_device = user_has_device(user)
    except ImportError:
        return False
    except Exception:  # noqa: BLE001 — apps/migrations may be absent
        # Package present but not wired into INSTALLED_APPS yet.
        return True
    # Enrollment grace: no device yet → allow admin so they can add one.
    if not has_device:
        return True
    return False


def patch_admin_site_for_otp(site) -> None:
    """
    Wrap ``site.has_permission`` so verified OTP is required when
    ``staff_2fa_enforced()`` is true.
    """
    if getattr(site, "_nova_otp_patched", False):
        return
    original = site.has_permission

    def has_permission(request):
        if not original(request):
            return False
        if not staff_2fa_enforced():
            return True
        return user_otp_verified(request)

    site.has_permission = has_permission
    site._nova_otp_patched = True
