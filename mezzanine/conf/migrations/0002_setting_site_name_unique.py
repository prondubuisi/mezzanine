from django.db import migrations, models
from django.db.models import Count


def dedupe_settings(apps, schema_editor):
    """Keep the highest id per (site_id, name); drop older duplicates (B8)."""
    Setting = apps.get_model("conf", "Setting")
    keys = (
        Setting.objects.values("site_id", "name")
        .annotate(n=Count("id"))
        .filter(n__gt=1)
    )
    for key in keys:
        ids = list(
            Setting.objects.filter(site_id=key["site_id"], name=key["name"])
            .order_by("-id")
            .values_list("id", flat=True)
        )
        # Keep first (newest); delete the rest.
        Setting.objects.filter(id__in=ids[1:]).delete()


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("conf", "0001_initial"),
        ("sites", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(dedupe_settings, noop),
        migrations.AddConstraint(
            model_name="setting",
            constraint=models.UniqueConstraint(
                fields=("site", "name"),
                name="nova_setting_site_name",
            ),
        ),
    ]
