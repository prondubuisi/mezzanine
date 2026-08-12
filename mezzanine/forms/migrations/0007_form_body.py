from django.db import migrations, models


def wrap_content(apps, schema_editor):
    Form = apps.get_model("forms", "Form")
    for obj in Form.objects.all().iterator():
        html = obj.content or ""
        body = {
            "$schema": "nova.document.v1",
            "blocks": ([{"type": "html", "html": html}] if html.strip() else []),
        }
        Form.objects.filter(pk=obj.pk).update(body=body)


class Migration(migrations.Migration):

    dependencies = [
        ("forms", "0006_auto_20170425_2225"),
    ]

    operations = [
        migrations.AddField(
            model_name="form",
            name="body",
            field=models.JSONField(blank=True, default=dict, verbose_name="Body"),
        ),
        migrations.RunPython(wrap_content, migrations.RunPython.noop),
    ]
