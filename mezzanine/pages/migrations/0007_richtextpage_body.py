from django.db import migrations, models


def wrap_content(apps, schema_editor):
    RichTextPage = apps.get_model("pages", "RichTextPage")
    for obj in RichTextPage.objects.all().iterator():
        html = obj.content or ""
        body = {
            "$schema": "nova.document.v1",
            "blocks": ([{"type": "html", "html": html}] if html.strip() else []),
        }
        RichTextPage.objects.filter(pk=obj.pk).update(body=body)


class Migration(migrations.Migration):

    dependencies = [
        ("pages", "0006_page_status_default_draft"),
    ]

    operations = [
        migrations.AddField(
            model_name="richtextpage",
            name="body",
            field=models.JSONField(blank=True, default=dict, verbose_name="Body"),
        ),
        migrations.RunPython(wrap_content, migrations.RunPython.noop),
    ]
