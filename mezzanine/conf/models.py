from django.db import models
from django.utils.translation import gettext_lazy as _

from mezzanine.core.models import SiteRelated


class Setting(SiteRelated):
    """
    Stores values for ``mezzanine.conf`` that can be edited via the admin.
    """

    name = models.CharField(max_length=50)
    value = models.CharField(max_length=2000)

    class Meta:
        verbose_name = _("Setting")
        verbose_name_plural = _("Settings")
        constraints = [
            models.UniqueConstraint(
                fields=["site", "name"],
                name="nova_setting_site_name",
            ),
        ]

    def __str__(self):
        return f"{self.name}: {self.value}"
