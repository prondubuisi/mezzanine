import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("contenttypes", "0002_remove_content_type_name"),
        ("core", "0006_media_is_public"),
    ]

    operations = [
        migrations.CreateModel(
            name="FieldSchema",
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
                ("kit", models.CharField(blank=True, default="", max_length=64)),
                ("name", models.CharField(max_length=64)),
                ("label", models.CharField(max_length=128)),
                (
                    "field_type",
                    models.CharField(
                        choices=[
                            ("text", "Text"),
                            ("richtext", "RichText"),
                            ("number", "Number"),
                            ("boolean", "Boolean"),
                            ("choice", "Choice"),
                            ("reference", "Reference"),
                        ],
                        default="text",
                        max_length=16,
                    ),
                ),
                ("required", models.BooleanField(default=False)),
                ("order", models.PositiveIntegerField(default=0)),
                ("options", models.JSONField(blank=True, default=dict)),
                (
                    "content_type",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="field_schemas",
                        to="contenttypes.contenttype",
                        verbose_name="Content type",
                    ),
                ),
            ],
            options={
                "verbose_name": "Field schema",
                "verbose_name_plural": "Field schemas",
                "ordering": ("order", "name"),
            },
        ),
        migrations.AddConstraint(
            model_name="fieldschema",
            constraint=models.UniqueConstraint(
                fields=("content_type", "name"),
                name="nova_fieldschema_ct_name",
            ),
        ),
    ]
