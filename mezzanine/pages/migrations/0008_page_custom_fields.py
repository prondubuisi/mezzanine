from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("pages", "0007_richtextpage_body"),
    ]

    operations = [
        migrations.AddField(
            model_name="page",
            name="custom_fields",
            field=models.JSONField(
                blank=True, default=dict, verbose_name="Custom fields"
            ),
        ),
    ]
