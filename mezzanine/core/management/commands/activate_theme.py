"""
Activate a first-party theme package (WordPress-style).

Usage::

    python manage.py activate_theme whitehouse
    python manage.py activate_theme spotify --seed
    python manage.py activate_theme --list
"""

from __future__ import annotations

from django.core.management.base import BaseCommand, CommandError

from mezzanine.kits.theme import (
    ThemeError,
    list_theme_names,
    load_theme_meta,
    set_active_theme,
    theme_plugins,
    theme_plugins_installed,
)


class Command(BaseCommand):
    help = "Set ACTIVE_THEME to a kit theme package (runtime chrome switch)."

    def add_arguments(self, parser):
        parser.add_argument(
            "name",
            nargs="?",
            help="Theme kit name (folder under mezzanine/kits/).",
        )
        parser.add_argument(
            "--list",
            action="store_true",
            dest="list_themes",
            help="List available theme packages.",
        )
        parser.add_argument(
            "--seed",
            action="store_true",
            help="Run theme seed_command or seed_profile after activate.",
        )

    def handle(self, *args, **options):
        if options["list_themes"]:
            for name in list_theme_names():
                meta = load_theme_meta(name)
                ready = theme_plugins_installed(meta)
                flag = "ready" if ready else "missing-plugins"
                self.stdout.write(
                    f"{name:16} {meta.get('version', '?'):8} [{flag}]  "
                    f"{meta.get('description', '')[:60]}"
                )
            return

        name = options.get("name")
        if not name:
            raise CommandError("Pass a theme name or --list")

        try:
            meta = set_active_theme(name)
        except ThemeError as exc:
            raise CommandError(str(exc)) from exc

        self.stdout.write(
            self.style.SUCCESS("ACTIVE_THEME = %s" % name)
        )
        plugins = theme_plugins(meta)
        if plugins:
            self.stdout.write("  plugins: %s" % ", ".join(plugins))
        slots = meta.get("slots") or {}
        if slots:
            self.stdout.write("  slots: %s" % ", ".join(sorted(slots)))

        if options["seed"]:
            seed_cmd = meta.get("seed_command")
            seed_profile = meta.get("seed_profile")
            # Also accept from kit.json if theme.json omitted them
            if not seed_cmd and not seed_profile:
                try:
                    from mezzanine.kits.loader import (
                        kit_seed_command,
                        kit_seed_profile,
                        load_kit_meta,
                    )

                    _, kit_meta = load_kit_meta(name)
                    seed_cmd = kit_seed_command(kit_meta)
                    seed_profile = kit_seed_profile(kit_meta)
                except Exception:  # noqa: BLE001
                    pass
            from django.core.management import call_command

            if seed_cmd:
                self.stdout.write("Seeding via %s --flush…" % seed_cmd)
                call_command(seed_cmd, flush=True)
            elif seed_profile:
                self.stdout.write(
                    "Seeding site profile %s…" % seed_profile
                )
                call_command(
                    "seed_site_clone", site=seed_profile, flush=True
                )
            else:
                self.stdout.write(
                    self.style.WARNING("No seed_command/seed_profile for theme.")
                )
