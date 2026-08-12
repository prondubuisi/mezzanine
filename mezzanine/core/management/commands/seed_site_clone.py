"""
Seed an IA clone of a well-known public site profile.

Usage::

    python manage.py seed_site_clone --site techcrunch
    python manage.py seed_site_clone --site time --flush
    python manage.py seed_site_clone --list
"""

from __future__ import annotations

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from mezzanine.core.document import body_from_html
from mezzanine.core.models import CONTENT_STATUS_PUBLISHED
from mezzanine.demos.seed_images import placeholder_png
from mezzanine.demos.site_profiles import get_profile, list_sites
from mezzanine.forms import fields as form_fields
from mezzanine.utils.seed import DEFAULT_SUPERUSER_USERNAME
from mezzanine.utils.sites import current_site_id


class Command(BaseCommand):
    help = "Seed pages/posts for a named site IA clone (TechCrunch, TIME, …)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--site",
            dest="site",
            help="Profile slug (techcrunch, time, whitehouse, …).",
        )
        parser.add_argument(
            "--list",
            action="store_true",
            dest="list_sites",
            help="List available site profile slugs.",
        )
        parser.add_argument(
            "--flush",
            action="store_true",
            help="Delete existing RichText pages, forms, and blog posts first.",
        )
        parser.add_argument(
            "--user",
            dest="username",
            default=DEFAULT_SUPERUSER_USERNAME,
            help=(
                "Author username for posts "
                f"(default: {DEFAULT_SUPERUSER_USERNAME})."
            ),
        )

    def handle(self, *args, **options):
        if options["list_sites"]:
            for slug in list_sites():
                profile = get_profile(slug)
                self.stdout.write(f"{slug:20} {profile['display_name']}")
            return

        slug = options.get("site")
        if not slug:
            raise CommandError("Pass --site SLUG or --list")

        try:
            profile = get_profile(slug)
        except KeyError as exc:
            raise CommandError(str(exc)) from exc

        if "mezzanine.pages" not in settings.INSTALLED_APPS:
            raise CommandError("mezzanine.pages is required")

        from mezzanine.forms.models import Field, Form
        from mezzanine.pages.models import RichTextPage

        site = Site.objects.get(id=current_site_id())
        Site.objects.filter(id=site.id).update(name=profile["site_name"][:50])
        # Best-effort: Mezzanine SITE_TITLE drives navbar brand, not django Site.name.
        try:
            from mezzanine.conf import settings as msettings
            from mezzanine.conf.models import Setting

            Setting.objects.update_or_create(
                name="SITE_TITLE",
                defaults={"value": profile["site_name"][:50]},
            )
            Setting.objects.update_or_create(
                name="SITE_TAGLINE",
                defaults={"value": profile.get("tagline", "")[:100]},
            )
            # Clear conf cache so next request sees new titles.
            if hasattr(msettings, "clear_cache"):
                msettings.clear_cache()
            elif hasattr(msettings, "_loaded"):
                msettings._loaded = False
        except Exception:  # noqa: BLE001 — conf app optional in odd test envs
            pass

        if options["flush"]:
            self.stdout.write("Flushing pages/posts/forms…")
            RichTextPage.objects.all().delete()
            if "mezzanine.blog" in settings.INSTALLED_APPS:
                from mezzanine.blog.models import BlogPost

                BlogPost.objects.all().delete()
            if "mezzanine.forms" in settings.INSTALLED_APPS:
                Form.objects.all().delete()

        self.stdout.write(
            self.style.NOTICE(
                "Seeding %s (inspired by %s)"
                % (profile["display_name"], profile["inspired_by"])
            )
        )

        order = 0
        now = timezone.now()
        from django.utils.text import slugify

        cat_by_title = {c.lower(): c for c in profile.get("categories", [])}
        for title, page_slug, html in profile["pages"]:
            # When section title matches a blog category, link to its archive (X2).
            if title.lower() in cat_by_title:
                cat_slug = slugify(cat_by_title[title.lower()])
                html = (
                    "%s<p><a href=\"/blog/category/%s/\">Browse %s posts →</a></p>"
                    % (html, cat_slug, title)
                )
            # Sync body JSON so re-seed without --flush updates content (B7).
            body = body_from_html(html)
            page, created = RichTextPage.objects.get_or_create(
                slug=page_slug,
                defaults={
                    "title": title,
                    "status": CONTENT_STATUS_PUBLISHED,
                    "content": html,
                    "body": body,
                    "in_menus": [1, 2, 3],
                    "_order": order,
                    "publish_date": now,
                },
            )
            if not created:
                page.title = title
                page.body = body
                page.content = html
                page.status = CONTENT_STATUS_PUBLISHED
                page.in_menus = [1, 2, 3]
                page._order = order
                page.save()
            order += 1
            self.stdout.write(f"  page: /{page_slug}/")

        if profile.get("contact") and "mezzanine.forms" in settings.INSTALLED_APPS:
            form_page, _ = Form.objects.get_or_create(
                slug="contact",
                defaults={
                    "title": "Contact",
                    "status": CONTENT_STATUS_PUBLISHED,
                    "content": "<p>Press and general contact for this demo.</p>",
                    "button_text": "Send",
                    "response": "<p>Thanks — message received.</p>",
                    "in_menus": [1, 2, 3],
                    "_order": order,
                    "publish_date": timezone.now(),
                },
            )
            if not form_page.fields.exists():
                Field.objects.create(
                    form=form_page,
                    label="Email",
                    field_type=form_fields.EMAIL,
                    required=True,
                    _order=0,
                )
                Field.objects.create(
                    form=form_page,
                    label="Message",
                    field_type=form_fields.TEXTAREA,
                    required=True,
                    _order=1,
                )
            self.stdout.write("  form: /contact/")

        if "mezzanine.blog" in settings.INSTALLED_APPS:
            from mezzanine.blog.models import BlogCategory, BlogPost

            User = get_user_model()
            try:
                author = User.objects.get(username=options["username"])
            except User.DoesNotExist:
                author = User.objects.filter(is_superuser=True).first()
            if author is None:
                raise CommandError("No user for blog posts; create a superuser first.")

            cat_map = {}
            for cat_title in profile.get("categories", []):
                cat, _ = BlogCategory.objects.get_or_create(title=cat_title)
                cat_map[cat_title] = cat

            from datetime import timedelta

            for i, (title, post_slug, cat_title, html) in enumerate(
                profile.get("posts", [])
            ):
                body = body_from_html(html)
                # Stagger publish dates so "latest" river ordering is meaningful (S1).
                pub = now - timedelta(days=len(profile.get("posts", [])) - i)
                post, created = BlogPost.objects.get_or_create(
                    slug=post_slug,
                    defaults={
                        "title": title,
                        "user": author,
                        "status": CONTENT_STATUS_PUBLISHED,
                        "content": html,
                        "body": body,
                        "publish_date": pub,
                        "allow_comments": False,
                    },
                )
                if not created:
                    post.title = title
                    post.body = body
                    post.content = html
                    post.status = CONTENT_STATUS_PUBLISHED
                    post.user = author
                    post.publish_date = pub
                    post.save()
                if cat_title in cat_map:
                    post.categories.add(cat_map[cat_title])
                # Featured image placeholders (S5 / parity backlog).
                if not post.featured_image:
                    try:
                        png = placeholder_png(post_slug)
                        rel = "blog/seed/%s.png" % post_slug
                        saved = default_storage.save(rel, ContentFile(png))
                        post.featured_image = saved
                        post.save(update_fields=["featured_image"])
                    except Exception as exc:  # noqa: BLE001 — seed continues
                        self.stdout.write(
                            self.style.WARNING(
                                "  featured image skip %s: %s" % (post_slug, exc)
                            )
                        )
                self.stdout.write(f"  post: {post_slug} [{cat_title}]")

        self.stdout.write(self.style.SUCCESS(f"Done: {slug}"))
        self.stdout.write("Parity notes for later:")
        for note in profile.get("notes", []):
            self.stdout.write(f"  - {note}")
