"""Gallery settings (Y1.5 zip-bomb limits)."""

from django.utils.translation import gettext_lazy as _

from mezzanine.conf import register_setting

register_setting(
    name="GALLERIES_ZIP_MAX_FILES",
    description=_("Maximum number of image entries imported from one zip."),
    editable=False,
    default=200,
)

register_setting(
    name="GALLERIES_ZIP_MAX_UNCOMPRESSED_BYTES",
    description=_(
        "Maximum total uncompressed size (bytes) allowed when importing "
        "a gallery zip (zip-bomb defense)."
    ),
    editable=False,
    default=50 * 1024 * 1024,  # 50 MiB
)

register_setting(
    name="GALLERIES_ZIP_MAX_ENTRY_BYTES",
    description=_("Maximum size of a single file inside a gallery zip."),
    editable=False,
    default=10 * 1024 * 1024,  # 10 MiB
)
