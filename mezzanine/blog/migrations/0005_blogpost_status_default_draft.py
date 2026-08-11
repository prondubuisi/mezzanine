from django.db import migrations, models


class Migration(migrations.Migration):
    """Default new blog posts to Draft. Existing rows are unchanged."""

    dependencies = [
        ("blog", "0004_blogpost_site_slug"),
    ]

    operations = [
        migrations.AlterField(
            model_name="blogpost",
            name="status",
            field=models.IntegerField(
                choices=[(1, "Draft"), (2, "Published")],
                default=1,
                help_text=(
                    "With Draft chosen, the public URL returns 404 unless a "
                    "preview token is used."
                ),
                verbose_name="Status",
            ),
        ),
    ]
