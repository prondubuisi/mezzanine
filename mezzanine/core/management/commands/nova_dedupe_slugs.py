"""Dedupe (site, slug) collisions on pages.Page and blog.BlogPost.

PR-021 adds UniqueConstraint(fields=["site", "slug"]) on those two
tables. Operators run ``nova_dedupe_slugs --dry-run`` to print
collisions, then without ``--dry-run`` (or the matching RunPython
migrations) rewrite extras so the constraint can be added.

Algorithm (Data Model Changes / PR-021):

* Group by ``(site_id, slug)`` on ``pages_page`` and ``blog_blogpost``.
* Keep the oldest ``id``; others become ``slug + "-" + id``.
* Page descendants (parent FK) get the same prefix rewrite as
  ``Page.set_slug``. We do not call ``set_slug`` while a peer still
  holds the colliding slug: that method matches ``slug + "/"``
  globally and would rewrite the keeper's children.
* Skip rows with ``content_model == "link"`` and slug starting with
  ``http`` (do not mutate external Link URLs).
* Postgres and SQLite only.
"""

from django.apps import apps
from django.core.management.base import BaseCommand, CommandError
from django.db import connection
from django.db.models import Count
from django.db.models.query import QuerySet

SUPPORTED_VENDORS = frozenset({"postgresql", "sqlite"})


def unscoped_qs(model):
    """All rows, all sites. Bypasses CurrentSiteManager on live models."""
    return QuerySet(model=model)


def is_http_link(obj):
    slug = obj.slug or ""
    return getattr(obj, "content_model", None) == "link" and slug.startswith(
        "http"
    )


def collision_groups(model):
    """Lists of instances sharing (site_id, slug), oldest id first."""
    qs = unscoped_qs(model)
    keys = (
        qs.values("site_id", "slug")
        .annotate(n=Count("id"))
        .filter(n__gt=1)
        .order_by("site_id", "slug")
    )
    groups = []
    for key in keys:
        objs = list(
            qs.filter(site_id=key["site_id"], slug=key["slug"]).order_by("id")
        )
        if len(objs) > 1:
            groups.append(objs)
    return groups


def _collect_descendant_rewrites(model, page, old_prefix, new_prefix):
    """
    Parent-FK descendants whose slug is prefixed by ``old_prefix``.

    Caveat (N4): walks children recursively with one query per node. Fine
    for operator-run one-off dedupe on typical trees; on very large page
    trees this can issue many queries — batch per level if it becomes a
    real pain point.
    """
    planned = []
    children = unscoped_qs(model).filter(parent_id=page.pk).order_by("id")
    for child in children:
        if is_http_link(child):
            continue
        child_slug = child.slug or ""
        if not child_slug.startswith(old_prefix + "/"):
            continue
        new_child_slug = new_prefix + child_slug[len(old_prefix) :]
        planned.append((child, child_slug, new_child_slug))
        planned.extend(
            _collect_descendant_rewrites(
                model, child, child_slug, new_child_slug
            )
        )
    return planned


def rewrite_page_slug(page, new_slug):
    """Rewrite ``page`` and its parent-FK descendants (set_slug rule)."""
    model = page.__class__
    old_slug = page.slug or ""
    for child, _old, child_new in _collect_descendant_rewrites(
        model, page, old_slug, new_slug
    ):
        child.slug = child_new
        child.save()
    page.slug = new_slug
    page.save()


def rewrite_blog_slug(post, new_slug):
    post.slug = new_slug
    post.save()


def _write(stdout, message):
    if stdout is not None:
        stdout.write(message)


def dedupe_model(
    model,
    *,
    dry_run,
    skip_fn,
    rewrite_fn,
    stdout=None,
    label=None,
):
    """Apply the keep-oldest / suffix-id rule. Returns (renamed, skipped)."""
    label = label or model._meta.db_table
    renamed = 0
    skipped = 0
    # Multiple passes: a rename of ``about`` to ``about-5`` may expose
    # or shift child collisions; suffix-by-id always changes the slug.
    for _pass in range(50):
        groups = collision_groups(model)
        groups.sort(key=lambda group: len(group[0].slug or ""))
        if not groups:
            if _pass == 0:
                _write(stdout, f"{label}: no (site, slug) collisions")
            break
        progressed = False
        for group in groups:
            keeper, *dupes = group
            site_id = keeper.site_id
            slug = keeper.slug
            _write(
                stdout,
                f"{label}: site_id={site_id} slug={slug!r}",
            )
            _write(stdout, f"  id={keeper.id} KEEP")
            for obj in dupes:
                if skip_fn is not None and skip_fn(obj):
                    skipped += 1
                    _write(
                        stdout,
                        f"  id={obj.id} SKIP content_model="
                        f"{getattr(obj, 'content_model', None)!r} http",
                    )
                    continue
                new_slug = f"{obj.slug}-{obj.id}"
                descendants = []
                if hasattr(obj, "parent_id"):
                    descendants = _collect_descendant_rewrites(
                        model, obj, obj.slug or "", new_slug
                    )
                _write(stdout, f"  id={obj.id} RENAME -> {new_slug!r}")
                for child, old_child, new_child in descendants:
                    _write(
                        stdout,
                        f"    child id={child.id} {old_child!r} -> {new_child!r}",
                    )
                if not dry_run:
                    rewrite_fn(obj, new_slug)
                    progressed = True
                renamed += 1
        if dry_run or not progressed:
            break
    return renamed, skipped


def remaining_collisions(model, skip_fn=None):
    """Collision groups that still have more than one non-skipped row."""
    leftover = []
    for group in collision_groups(model):
        actionable = [
            obj
            for obj in group
            if skip_fn is None or not skip_fn(obj)
        ]
        skipped = [obj for obj in group if skip_fn is not None and skip_fn(obj)]
        if len(actionable) > 1 or (skipped and len(group) > 1):
            leftover.append(group)
    return leftover


def dedupe_pages(model=None, dry_run=False, stdout=None):
    if model is None:
        from mezzanine.pages.models import Page

        model = Page
    return dedupe_model(
        model,
        dry_run=dry_run,
        skip_fn=is_http_link,
        rewrite_fn=rewrite_page_slug,
        stdout=stdout,
        label=model._meta.db_table,
    )


def dedupe_blog(model=None, dry_run=False, stdout=None):
    if model is None:
        from mezzanine.blog.models import BlogPost

        model = BlogPost
    return dedupe_model(
        model,
        dry_run=dry_run,
        skip_fn=None,
        rewrite_fn=rewrite_blog_slug,
        stdout=stdout,
        label=model._meta.db_table,
    )


def ensure_supported_vendor(vendor=None):
    vendor = vendor or connection.vendor
    if vendor not in SUPPORTED_VENDORS:
        raise CommandError(
            "UniqueConstraint(site, slug) is supported on PostgreSQL and "
            f"SQLite only (this database vendor is {vendor!r})."
        )
    return vendor


def check_remaining(model, skip_fn, label):
    leftover = remaining_collisions(model, skip_fn=skip_fn)
    if not leftover:
        return
    details = []
    for group in leftover:
        slug = group[0].slug
        site_id = group[0].site_id
        ids = ", ".join(str(obj.id) for obj in group)
        details.append(f"{label} site_id={site_id} slug={slug!r} ids=[{ids}]")
    raise CommandError(
        "Collisions remain after dedupe (http Link slugs are skipped "
        "and must be resolved by hand before UniqueConstraint):\n  "
        + "\n  ".join(details)
    )


class Command(BaseCommand):
    help = (
        "Print or rewrite (site, slug) collisions on pages.Page and "
        "blog.BlogPost so UniqueConstraint(site, slug) can be applied."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            dest="dry_run",
            help="Print collisions without rewriting slugs.",
        )

    def handle(self, *args, **options):
        ensure_supported_vendor()
        dry_run = options["dry_run"]
        stdout = self.stdout

        from mezzanine.pages.models import Page

        dedupe_pages(Page, dry_run=dry_run, stdout=stdout)
        if not dry_run:
            check_remaining(Page, is_http_link, Page._meta.db_table)

        if apps.is_installed("mezzanine.blog"):
            from mezzanine.blog.models import BlogPost

            dedupe_blog(BlogPost, dry_run=dry_run, stdout=stdout)
            if not dry_run:
                check_remaining(BlogPost, None, BlogPost._meta.db_table)

        if dry_run:
            self.stdout.write("dry-run: no slugs rewritten")
        else:
            self.stdout.write(self.style.SUCCESS("dedupe complete"))
