from socket import gethostname

from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import connection

from mezzanine.conf import settings
from mezzanine.utils.tests import copy_test_to_media

DEFAULT_USERNAME = "admin"
DEFAULT_EMAIL = "example@example.com"
DEFAULT_PASSWORD = "default"


class Command(BaseCommand):

    help = "Performs initial Mezzanine database setup."
    can_import_settings = True

    def add_arguments(self, parser):
        """
        Adds extra command options (executed only by Django >= 1.8).
        """
        parser.add_argument(
            "--nodata", action="store_true", dest="nodata", help="Do not add demo data."
        )
        parser.add_argument(
            "--noinput",
            action="store_false",
            dest="interactive",
            help="Do not prompt the user for input of any kind.",
        )

    def handle(self, **options):

        if "conf_setting" in connection.introspection.table_names():
            raise CommandError(
                "Database already created, you probably " "want the migrate command"
            )

        self.verbosity = int(options.get("verbosity", 0))
        self.interactive = int(options.get("interactive", 0))
        self.no_data = int(options.get("nodata", 0))

        call_command("migrate", verbosity=self.verbosity, interactive=self.interactive)

        mapping = [
            [self.create_site, ["django.contrib.sites"]],
            [self.create_user, ["django.contrib.auth"]],
            [self.translation_fields, ["modeltranslation"]],
            # pages alone is enough — brochure installs pages+forms without
            # blog/galleries (PR-032). create_pages branches on kit apps.
            [self.create_pages, ["mezzanine.pages"]],
            [self.create_shop, ["cartridge.shop"]],
        ]

        for func, apps in mapping:
            if set(apps).issubset(set(settings.INSTALLED_APPS)):
                func()

    def confirm(self, prompt):
        if not self.interactive:
            return True
        confirm = input(prompt)
        while confirm not in ("yes", "no"):
            confirm = input("Please enter either 'yes' or 'no': ")
        return confirm == "yes"

    def create_site(self):
        domain = "127.0.0.1:8000" if settings.DEBUG else gethostname()
        if self.interactive:
            entered = input(
                "\nA site record is required.\nPlease "
                "enter the domain and optional port in "
                "the format 'domain:port'.\nFor example "
                "'localhost:8000' or 'www.example.com'. "
                "\nHit enter to use the default (%s): " % domain
            )
            if entered:
                domain = entered.strip("': ")
        if self.verbosity >= 1:
            print("\nCreating default site record: %s ...\n" % domain)
        try:
            site = Site.objects.get()
        except Site.DoesNotExist:
            site = Site()
        site.name = "Default"
        site.domain = domain
        site.save()

    def create_user(self):
        User = get_user_model()
        if User.objects.count() > 0:
            return
        if self.interactive:
            if self.verbosity >= 1:
                print("\nCreating default account ...\n")
            call_command("createsuperuser")
            return
        if not settings.DEBUG:
            raise CommandError(
                "Refusing to create the default account "
                "(%s / %s) when DEBUG=False. "
                "Re-run createdb interactively or use createsuperuser."
                % (DEFAULT_USERNAME, DEFAULT_PASSWORD)
            )
        if self.verbosity >= 1:
            print(
                "\nCreating default account "
                "(username: %s / password: %s) ...\n"
                % (DEFAULT_USERNAME, DEFAULT_PASSWORD)
            )
        args = (DEFAULT_USERNAME, DEFAULT_EMAIL, DEFAULT_PASSWORD)
        User.objects.create_superuser(*args)

    def create_pages(self):
        # First-party kits: seed_profile (kit.json), special commands, or fixtures.
        kit_apps = (
            (
                "mezzanine.kits.spotify",
                "Spotify Web Player–style",
                "Music UI demo (catalog data; no seed required).",
            ),
            (
                "mezzanine.kits.whitehouse",
                "White House–style",
                "Briefing room: releases, briefings, actions (seed_site_clone).",
            ),
            (
                "mezzanine.kits.wporg",
                "wordpress.org-style",
                "Features, Learn, Community, News, Get started (seed_wporg_demo).",
            ),
            ("mezzanine.kits.brochure", "Brochure", "About, Services, Contact form."),
            (
                "mezzanine.kits.magazine",
                "Magazine",
                "About, Contact form, and a sample blog post.",
            ),
            (
                "mezzanine.kits.institute",
                "Institute",
                "Higher-ed pages + news (demo fixture).",
            ),
        )
        for app_label, label, desc in kit_apps:
            if app_label not in settings.INSTALLED_APPS:
                continue
            if self.no_data:
                return
            install = self.confirm(
                f"\nWould you like to install {label} demo content?\n"
                f"{desc} (yes/no): "
            )
            if install:
                if self.verbosity >= 1:
                    print(f"\nLoading {label} demo content ...\n")
                kit_name = app_label.rsplit(".", 1)[-1]
                seed_profile = None
                try:
                    from mezzanine.kits.loader import kit_seed_profile, load_kit_meta

                    _, meta = load_kit_meta(kit_name)
                    seed_profile = kit_seed_profile(meta)
                except Exception:  # noqa: BLE001 — fall back to fixtures
                    seed_profile = None
                if seed_profile:
                    call_command("seed_site_clone", site=seed_profile)
                elif app_label == "mezzanine.kits.wporg":
                    call_command("seed_wporg_demo")
                else:
                    call_command("loaddata", "demo")
                    if app_label == "mezzanine.kits.magazine":
                        self._seed_magazine_blog_post()
            return

        # Required fixture is pages-only. Optional dump spans pages + forms +
        # galleries fixtures of the same name; only load when all three apps
        # are installed so gallery/form MTI rows resolve.
        call_command("loaddata", "mezzanine_required.json")
        optional_apps = ("mezzanine.forms", "mezzanine.galleries")
        if not set(optional_apps).issubset(settings.INSTALLED_APPS):
            return
        install_optional = not self.no_data and self.confirm(
            "\nWould you like to install some initial "
            "demo pages?\nEg: About us, Contact form, "
            "Gallery. (yes/no): "
        )
        if not install_optional:
            return
        if self.verbosity >= 1:
            print("\nCreating demo pages: About us, Contact form, " "Gallery ...\n")
        call_command("loaddata", "mezzanine_optional.json")
        from mezzanine.galleries.models import Gallery

        zip_name = "gallery.zip"
        copy_test_to_media("mezzanine.core", zip_name)
        gallery = Gallery.objects.get()
        gallery.zip_import = zip_name
        gallery.save()

    def _seed_magazine_blog_post(self):
        """Create one published sample post for Magazine kit demos."""
        if "mezzanine.blog" not in settings.INSTALLED_APPS:
            return
        from django.contrib.auth import get_user_model

        from mezzanine.blog.models import BlogPost
        from mezzanine.core.models import CONTENT_STATUS_PUBLISHED

        if BlogPost.objects.exists():
            return
        user = get_user_model().objects.order_by("id").first()
        if user is None:
            return
        BlogPost.objects.create(
            title="Welcome to the magazine",
            user=user,
            content=(
                "<p>This is a sample editorial post. Replace it with your "
                "own WordPress import or write new posts in admin.</p>"
            ),
            status=CONTENT_STATUS_PUBLISHED,
        )
        if self.verbosity >= 1:
            print("Created sample magazine blog post.\n")

    def create_shop(self):
        call_command("loaddata", "cartridge_required.json")
        install_optional = not self.no_data and self.confirm(
            "\nWould you like to install an initial "
            "demo product and sale? (yes/no): "
        )
        if install_optional:
            if self.verbosity >= 1:
                print("\nCreating demo product and sale ...\n")
            call_command("loaddata", "cartridge_optional.json")
            copy_test_to_media("cartridge.shop", "product")

    def translation_fields(self):
        try:
            from modeltranslation.management.commands import (
                sync_translation_fields as create_fields,
            )
            from modeltranslation.management.commands import (
                update_translation_fields as update_fields,
            )
        except ImportError:
            return
        update = self.confirm(
            "\nDjango-modeltranslation is installed for "
            "this project and you have specified to use "
            "i18n.\nWould you like to update translation "
            "fields from the default ones? (yes/no): "
        )
        if update:
            options = {
                "verbosity": self.verbosity,
                "interactive": self.interactive,
            }
            call_command(create_fields.Command(), **options)
            call_command(update_fields.Command(), **options)
