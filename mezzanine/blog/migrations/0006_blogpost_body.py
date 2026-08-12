from django.db import migrations, models


def wrap_content(apps, schema_editor):
    BlogPost = apps.get_model("blog", "BlogPost")
    for obj in BlogPost.objects.all().iterator():
        html = obj.content or ""
        body = {
            "$schema": "nova.document.v1",
            "blocks": ([{"type": "html", "html": html}] if html.strip() else []),
        }
        BlogPost.objects.filter(pk=obj.pk).update(body=body)


class Migration(migrations.Migration):

    dependencies = [
        ("blog", "0005_blogpost_status_default_draft"),
    ]

    operations = [
        migrations.AddField(
            model_name="blogpost",
            name="body",
            field=models.JSONField(blank=True, default=dict, verbose_name="Body"),
        ),
        migrations.RunPython(wrap_content, migrations.RunPython.noop),
    ]
