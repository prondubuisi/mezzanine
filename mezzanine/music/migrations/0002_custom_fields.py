from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("music", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="album",
            name="custom_fields",
            field=models.JSONField(
                blank=True, default=dict, verbose_name="Custom fields"
            ),
        ),
        migrations.AddField(
            model_name="artist",
            name="custom_fields",
            field=models.JSONField(
                blank=True, default=dict, verbose_name="Custom fields"
            ),
        ),
        migrations.AddField(
            model_name="playlist",
            name="custom_fields",
            field=models.JSONField(
                blank=True, default=dict, verbose_name="Custom fields"
            ),
        ),
        migrations.AddField(
            model_name="track",
            name="custom_fields",
            field=models.JSONField(
                blank=True, default=dict, verbose_name="Custom fields"
            ),
        ),
    ]
