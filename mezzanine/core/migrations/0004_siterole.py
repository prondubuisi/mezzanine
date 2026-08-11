from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def explode_sitepermission(apps, schema_editor):
    SitePermission = apps.get_model("core", "SitePermission")
    SiteRole = apps.get_model("core", "SiteRole")
    for perm in SitePermission.objects.all().iterator():
        for site in perm.sites.all():
            SiteRole.objects.get_or_create(
                user_id=perm.user_id,
                site_id=site.pk,
                defaults={"role": "editor"},
            )


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("sites", "0002_alter_domain_unique"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("core", "0003_previewtoken"),
    ]

    operations = [
        migrations.CreateModel(
            name="SiteRole",
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
                (
                    "role",
                    models.CharField(
                        choices=[
                            ("author", "Author"),
                            ("editor", "Editor"),
                            ("publisher", "Publisher"),
                            ("admin", "Admin"),
                        ],
                        default="editor",
                        max_length=16,
                    ),
                ),
                (
                    "site",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="siteroles",
                        to="sites.site",
                        verbose_name="Site",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="siteroles",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="User",
                    ),
                ),
            ],
            options={
                "verbose_name": "Site role",
                "verbose_name_plural": "Site roles",
            },
        ),
        migrations.AddConstraint(
            model_name="siterole",
            constraint=models.UniqueConstraint(
                fields=("user", "site"), name="nova_siterole_user_site"
            ),
        ),
        migrations.RunPython(explode_sitepermission, noop),
        migrations.DeleteModel(name="SitePermission"),
    ]
