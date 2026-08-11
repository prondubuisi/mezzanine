from django.db import migrations, models


def dedupe_blogpost_slugs(apps, schema_editor):
    vendor = schema_editor.connection.vendor
    if vendor not in ("postgresql", "sqlite"):
        raise RuntimeError(
            "UniqueConstraint(site, slug) is supported on PostgreSQL and "
            f"SQLite only (this database vendor is {vendor!r})."
        )
    from mezzanine.core.management.commands.nova_dedupe_slugs import (
        check_remaining,
        dedupe_blog,
    )

    BlogPost = apps.get_model("blog", "BlogPost")
    dedupe_blog(BlogPost, dry_run=False)
    check_remaining(BlogPost, None, BlogPost._meta.db_table)


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("blog", "0003_auto_20170411_0504"),
    ]

    operations = [
        migrations.RunPython(dedupe_blogpost_slugs, noop),
        migrations.AddConstraint(
            model_name="blogpost",
            constraint=models.UniqueConstraint(
                fields=("site", "slug"),
                name="blogpost_site_slug",
            ),
        ),
    ]
