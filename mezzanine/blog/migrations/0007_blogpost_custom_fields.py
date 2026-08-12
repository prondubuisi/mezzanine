from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("blog", "0006_blogpost_body"),
    ]

    operations = [
        migrations.AddField(
            model_name="blogpost",
            name="custom_fields",
            field=models.JSONField(
                blank=True, default=dict, verbose_name="Custom fields"
            ),
        ),
    ]
