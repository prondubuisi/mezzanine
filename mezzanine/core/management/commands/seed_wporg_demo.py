"""
Seed a wordpress.org–inspired marketing site (IA PoC).

Creates pages + blog posts matching a popular open-source CMS marketing
shape: Features, Learn, Hosting, Community, About, Get started, Contact,
and a News blog. Content is original; structure is inspired by
wordpress.org public navigation — not a trademarked clone.

Usage::

    python manage.py seed_wporg_demo
    python manage.py seed_wporg_demo --flush
"""

from __future__ import annotations

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from mezzanine.core.models import CONTENT_STATUS_PUBLISHED
from mezzanine.forms import fields as form_fields
from mezzanine.utils.sites import current_site_id


class Command(BaseCommand):
    help = (
        "Seed pages + news posts recreating a wordpress.org–style marketing IA "
        "(PoC for WP → Nova)."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--flush",
            action="store_true",
            help="Delete existing RichText pages / blog posts for this site first.",
        )
        parser.add_argument(
            "--user",
            dest="username",
            default="admin",
            help="Author username for blog posts (default: admin).",
        )

    def handle(self, *args, **options):
        if "mezzanine.pages" not in settings.INSTALLED_APPS:
            raise CommandError("mezzanine.pages is required")

        from mezzanine.forms.models import Field, Form
        from mezzanine.pages.models import RichTextPage

        site = Site.objects.get(id=current_site_id())
        if site.name in ("example.com", "Example", ""):
            Site.objects.filter(id=site.id).update(name="Open Publish")

        if options["flush"]:
            self.stdout.write("Flushing pages and posts for current site…")
            RichTextPage.objects.all().delete()
            if "mezzanine.blog" in settings.INSTALLED_APPS:
                from mezzanine.blog.models import BlogPost

                BlogPost.objects.all().delete()
            if "mezzanine.forms" in settings.INSTALLED_APPS:
                Form.objects.all().delete()

        pages = [
            (
                "Features",
                "features",
                "<p>Block editor dual stacks, theme.json, and 69k plugins are "
                "someone else’s gravity well. Nova ships <strong>typed pages</strong>, "
                "bleach-on-read HTML, scheduled publish, and a Media library without "
                "filebrowser as identity.</p>"
                "<ul><li>Hierarchical page tree</li>"
                "<li>Draft by default + opaque preview tokens</li>"
                "<li>Adult WordPress WXR import with URL redirects</li>"
                "<li>Optional TinyMCE 7 CDN, staff TOTP, Postgres FTS</li></ul>",
            ),
            (
                "Learn",
                "learn",
                "<p>Friday path:</p>"
                "<pre>uvx nova-project mysite --kit wporg\n"
                "cd mysite &amp;&amp; just bootstrap &amp;&amp; just up\n"
                "python manage.py seed_wporg_demo</pre>"
                "<p>Import an existing WXR export with "
                "<code>just import-wp ./export.xml</code>.</p>",
            ),
            (
                "Hosting",
                "hosting",
                "<p>Nova is a Django app. Host it like any Django site: "
                "Postgres, Redis, gunicorn/uvicorn, object storage for media. "
                "Compose files ship for local Friday install; production is "
                "your platform (Fly, Render, k8s, bare metal).</p>",
            ),
            (
                "Community",
                "community",
                "<p>Discuss on GitHub issues. Security reports go privately to "
                "the address in the README. Code of conduct: Django’s.</p>",
            ),
            (
                "About",
                "about",
                "<p>This site is a <strong>proof of concept</strong>: the public "
                "IA of a popular open-source CMS marketing site, rebuilt on "
                "Nova (import path <code>mezzanine</code>, package "
                "<code>nova-cms</code>). It is not affiliated with Automattic "
                "or WordPress.org.</p>",
            ),
            (
                "Get started",
                "get-started",
                "<p>Install Nova, pick a kit, migrate, publish.</p>"
                "<ol><li><code>pip install 'nova-cms[migrate]'</code> "
                "(or monorepo <code>NOVA_CMS_SRC</code>)</li>"
                "<li><code>nova-project mysite --kit wporg</code></li>"
                "<li><code>just bootstrap &amp;&amp; just up</code></li>"
                "<li><code>python manage.py seed_wporg_demo</code></li></ol>"
                "<p>Or migrate from WordPress: export WXR → "
                "<code>just import-wp export.xml</code>.</p>",
            ),
        ]

        order = 0
        for title, slug, html in pages:
            page, created = RichTextPage.objects.get_or_create(
                slug=slug,
                defaults={
                    "title": title,
                    "status": CONTENT_STATUS_PUBLISHED,
                    "content": html,
                    "in_menus": [1, 2, 3],
                    "_order": order,
                    "publish_date": timezone.now(),
                },
            )
            if not created:
                page.title = title
                page.content = html
                page.status = CONTENT_STATUS_PUBLISHED
                page.in_menus = [1, 2, 3]
                page._order = order
                page.save()
            order += 1
            self.stdout.write(f"  page: /{slug}/")

        # Contact form (replaces many WP contact plugins).
        if "mezzanine.forms" in settings.INSTALLED_APPS:
            form_page, _ = Form.objects.get_or_create(
                slug="contact",
                defaults={
                    "title": "Contact",
                    "status": CONTENT_STATUS_PUBLISHED,
                    "content": (
                        "<p>Questions about the Nova demo? Send a note.</p>"
                    ),
                    "button_text": "Send",
                    "response": "<p>Thanks — we received your message.</p>",
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
                raise CommandError(
                    "No user for blog posts; create a superuser first."
                )

            news, _ = BlogCategory.objects.get_or_create(title="News")
            posts = [
                (
                    "Hello world (from Nova)",
                    "hello-world",
                    "<p>Every WordPress site starts with Hello world. "
                    "This post is the Nova equivalent — published as a typed "
                    "<code>BlogPost</code>, not a plugin post type.</p>",
                ),
                (
                    "Why marketing sites leave plugin gravity wells",
                    "why-leave-plugin-gravity",
                    "<p>Sixty-nine thousand plugins is a labor market, not a "
                    "product strategy. Typed models, default draft, and a "
                    "single import report beat an abandoned page-builder stack "
                    "for teams that already write Python.</p>",
                ),
                (
                    "Friday install: brochure to wordpress.org-shaped demo",
                    "friday-install-wporg-demo",
                    "<p>One kit flag, one seed command, and you have Features, "
                    "Learn, Community, News, and Get started — the shape "
                    "visitors expect from a major open-source CMS home.</p>",
                ),
            ]
            for title, slug, html in posts:
                post, created = BlogPost.objects.get_or_create(
                    slug=slug,
                    defaults={
                        "title": title,
                        "user": author,
                        "status": CONTENT_STATUS_PUBLISHED,
                        "content": html,
                        "publish_date": timezone.now(),
                        "allow_comments": False,
                    },
                )
                if not created:
                    post.title = title
                    post.content = html
                    post.status = CONTENT_STATUS_PUBLISHED
                    post.user = author
                    post.save()
                post.categories.add(news)
                self.stdout.write(f"  post: {slug}")

        self.stdout.write(self.style.SUCCESS("wporg demo seed complete."))
