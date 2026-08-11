from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("contenttypes", "0002_remove_content_type_name"),
        ("sites", "0002_alter_domain_unique"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("core", "0002_auto_20150414_2140"),
    ]

    operations = [
        migrations.CreateModel(
            name="PreviewToken",
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
                ("token_hash", models.CharField(max_length=64, unique=True)),
                ("object_pk", models.TextField()),
                (
                    "as_role",
                    models.CharField(
                        choices=[("anon", "anon"), ("staff", "staff")],
                        default="anon",
                        max_length=8,
                    ),
                ),
                ("expires_at", models.DateTimeField()),
                (
                    "last_seen_at",
                    models.DateTimeField(blank=True, null=True),
                ),
                (
                    "content_type",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="preview_tokens",
                        to="contenttypes.contenttype",
                    ),
                ),
                (
                    "created_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="preview_tokens",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "site",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="preview_tokens",
                        to="sites.site",
                    ),
                ),
            ],
            options={
                "verbose_name": "Preview token",
                "verbose_name_plural": "Preview tokens",
            },
        ),
    ]
