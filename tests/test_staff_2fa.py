"""PR-023b: optional staff TOTP (NOVA_STAFF_2FA), off by default."""

import os
from unittest import mock

import pytest
from django.test import RequestFactory, override_settings

from mezzanine.core import staff_2fa
from tests.factories import SuperUserFactory


@pytest.fixture(autouse=True)
def _clear_otp_cache():
    staff_2fa.django_otp_available.cache_clear()
    yield
    staff_2fa.django_otp_available.cache_clear()


def test_staff_2fa_off_by_default(settings):
    settings.NOVA_STAFF_2FA = False
    with mock.patch.dict(os.environ, {}, clear=False):
        os.environ.pop("NOVA_STAFF_2FA", None)
        assert staff_2fa.staff_2fa_setting_on() is False
        assert staff_2fa.staff_2fa_enforced() is False


def test_staff_2fa_env_enables_setting():
    with mock.patch.dict(os.environ, {"NOVA_STAFF_2FA": "1"}):
        assert staff_2fa.staff_2fa_setting_on() is True


def test_otp_extra_declared_in_pyproject():
    from pathlib import Path

    import mezzanine

    root = Path(mezzanine.__file__).resolve().parent.parent
    text = (root / "pyproject.toml").read_text(encoding="utf-8")
    assert "otp = [" in text
    assert "django-otp" in text


def test_django_otp_available_in_test_env():
    # testing extra installs django-otp; availability must be True here.
    staff_2fa.django_otp_available.cache_clear()
    assert staff_2fa.django_otp_available() is True


@override_settings(NOVA_STAFF_2FA=True)
def test_enforced_when_flag_and_package():
    staff_2fa.django_otp_available.cache_clear()
    with mock.patch.dict(os.environ, {"NOVA_STAFF_2FA": "1"}):
        assert staff_2fa.staff_2fa_enforced() is True


@override_settings(NOVA_STAFF_2FA=True)
def test_check_errors_when_package_missing():
    from mezzanine.core.checks import check_staff_2fa_package

    staff_2fa.django_otp_available.cache_clear()
    with mock.patch.dict(os.environ, {"NOVA_STAFF_2FA": "1"}):
        with mock.patch(
            "mezzanine.core.staff_2fa.staff_2fa_setting_on", return_value=True
        ):
            with mock.patch(
                "mezzanine.core.staff_2fa.django_otp_available", return_value=False
            ):
                errors = check_staff_2fa_package(None)
    assert len(errors) == 1
    assert errors[0].id == "mezzanine.core.E02"


@pytest.mark.django_db
def test_user_without_device_passes_enrollment_grace():
    user = SuperUserFactory(username="otpgrace", email="g@example.com")
    rf = RequestFactory()
    request = rf.get("/admin/")
    request.user = user
    # No OTPMiddleware → no is_verified; still grace if no devices.
    assert staff_2fa.user_otp_verified(request) is True


@pytest.mark.django_db
def test_user_with_device_requires_verification():
    pytest.importorskip("django_otp")
    user = SuperUserFactory(username="otpuser", email="o@example.com")
    rf = RequestFactory()
    request = rf.get("/admin/")
    request.user = user
    # Device registered but session not verified → deny.
    with mock.patch("django_otp.user_has_device", return_value=True):
        assert staff_2fa.user_otp_verified(request) is False

    # Simulate OTPMiddleware marking the user verified.
    user.is_verified = lambda: True  # type: ignore[method-assign]
    request.user = user
    with mock.patch("django_otp.user_has_device", return_value=True):
        assert staff_2fa.user_otp_verified(request) is True


def test_admin_has_permission_patched_when_enforced():
    from django.contrib import admin

    site = admin.site
    staff_2fa.patch_admin_site_for_otp(site)
    assert getattr(site, "_nova_otp_patched", False) is True
    # Idempotent
    staff_2fa.patch_admin_site_for_otp(site)
