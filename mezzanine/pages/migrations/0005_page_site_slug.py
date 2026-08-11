from django.db import migrations, models


def dedupe_page_slugs(apps, schema_editor):
    vendor = schema_editor.connection.vendor
    if vendor not in ("postgresql", "sqlite"):
        raise RuntimeError(
            "UniqueConstraint(site, slug) is supported on PostgreSQL and "
            f"SQLite only (this database vendor is {vendor!r})."
        )
    from mezzanine.core.management.commands.nova_dedupe_slugs import (
        check_remaining,
        dedupe_pages,
        is_http_link,
    )

    Page = apps.get_model("pages", "Page")
    dedupe_pages(Page, dry_run=False)
    check_remaining(Page, is_http_link, Page._meta.db_table)


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("pages", "0004_auto_20170411_0504"),
    ]

    operations = [
        migrations.RunPython(dedupe_page_slugs, noop),
        migrations.AddConstraint(
            model_name="page",
            constraint=models.UniqueConstraint(
                fields=("site", "slug"),
                name="page_site_slug",
            ),
        ),
    ]
