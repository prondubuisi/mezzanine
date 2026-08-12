from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0005_media_model"),
    ]

    operations = [
        migrations.AddField(
            model_name="media",
            name="is_public",
            field=models.BooleanField(
                default=False,
                help_text=(
                    "Allow unauthenticated clients to read metadata for this "
                    "asset. Does not put the file in the page tree or sitemap."
                ),
                verbose_name="Public",
            ),
        ),
    ]
