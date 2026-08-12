from django.db import migrations, models
import django.db.models.deletion
import mezzanine.core.models


class Migration(migrations.Migration):

    dependencies = [
        ("sites", "0002_alter_domain_unique"),
        ("core", "0004_siterole"),
    ]

    operations = [
        migrations.CreateModel(
            name="Media",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("title", models.CharField(blank=True, max_length=500, verbose_name="Title")),
                (
                    "file",
                    models.FileField(
                        max_length=255,
                        upload_to=mezzanine.core.models._media_upload_to,
                        verbose_name="File",
                    ),
                ),
                (
                    "alt",
                    models.CharField(
                        help_text="Required accessible description of the file.",
                        max_length=255,
                        verbose_name="Alt text",
                    ),
                ),
                (
                    "created",
                    models.DateTimeField(auto_now_add=True, verbose_name="Created"),
                ),
                (
                    "updated",
                    models.DateTimeField(auto_now=True, verbose_name="Updated"),
                ),
                (
                    "site",
                    models.ForeignKey(
                        editable=False,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="sites.site",
                    ),
                ),
            ],
            options={
                "verbose_name": "Media",
                "verbose_name_plural": "Media",
                "ordering": ("-created",),
            },
        ),
    ]
