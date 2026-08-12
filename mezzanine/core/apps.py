from django.apps import AppConfig


class CoreConfig(AppConfig):

    name = "mezzanine.core"

    def ready(self):
        from . import checks  # noqa

        # PR-023b: gate admin on verified OTP when NOVA_STAFF_2FA is on.
        try:
            from django.contrib import admin

            from mezzanine.core.staff_2fa import (
                patch_admin_site_for_otp,
                staff_2fa_enforced,
            )

            if staff_2fa_enforced():
                patch_admin_site_for_otp(admin.site)
        except Exception:  # noqa: BLE001 — never break app load for 2FA wire-up
            pass
