from django.db import migrations, models


def wrap_content(apps, schema_editor):
    Gallery = apps.get_model("galleries", "Gallery")
    for obj in Gallery.objects.all().iterator():
        html = obj.content or ""
        body = {
            "$schema": "nova.document.v1",
            "blocks": ([{"type": "html", "html": html}] if html.strip() else []),
        }
        Gallery.objects.filter(pk=obj.pk).update(body=body)


class Migration(migrations.Migration):

    dependencies = [
        ("galleries", "0002_auto_20141227_0224"),
    ]

    operations = [
        migrations.AddField(
            model_name="gallery",
            name="body",
            field=models.JSONField(blank=True, default=dict, verbose_name="Body"),
        ),
        migrations.RunPython(wrap_content, migrations.RunPython.noop),
    ]
