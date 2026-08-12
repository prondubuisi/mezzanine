import os
from io import BytesIO
from string import punctuation
from zipfile import BadZipFile, ZipFile

from chardet import detect as charsetdetect
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.db import models
from django.utils.encoding import force_str
from django.utils.translation import gettext
from django.utils.translation import gettext_lazy as _

from mezzanine.conf import settings
from mezzanine.core.fields import FileField
from mezzanine.core.models import DocumentBody, Orderable, RichText
from mezzanine.pages.models import Page
from mezzanine.utils.importing import import_dotted_path
from mezzanine.utils.models import upload_to

# Set the directory where gallery images are uploaded to,
# either MEDIA_ROOT + 'galleries', or filebrowser's upload
# directory if being used.
GALLERIES_UPLOAD_DIR = "galleries"
if settings.PACKAGE_NAME_FILEBROWSER in settings.INSTALLED_APPS:
    fb_settings = "%s.settings" % settings.PACKAGE_NAME_FILEBROWSER
    try:
        GALLERIES_UPLOAD_DIR = import_dotted_path(fb_settings).DIRECTORY
    except ImportError:
        pass


class BaseGallery(models.Model):
    """
    Base gallery functionality.
    """

    class Meta:
        abstract = True

    zip_import = models.FileField(
        verbose_name=_("Zip import"),
        blank=True,
        upload_to=upload_to("galleries.Gallery.zip_import", "galleries"),
        help_text=_(
            "Upload a zip file containing images, and "
            "they'll be imported into this gallery."
        ),
    )

    def _zip_limits(self):
        # Registered in galleries/defaults.py — no getattr fallbacks (H3).
        max_files = int(settings.GALLERIES_ZIP_MAX_FILES)
        max_total = int(settings.GALLERIES_ZIP_MAX_UNCOMPRESSED_BYTES)
        max_entry = int(settings.GALLERIES_ZIP_MAX_ENTRY_BYTES)
        return max_files, max_total, max_entry

    @staticmethod
    def _safe_zip_member_name(name: str) -> str | None:
        """Return basename only; reject path traversal / absolute paths."""
        if not name or name.endswith("/"):
            return None
        # Zip-slip: reject .. and absolute-style members.
        norm = name.replace("\\", "/")
        if norm.startswith("/") or ".." in norm.split("/"):
            return None
        base = os.path.split(norm)[1]
        if not base or base in (".", ".."):
            return None
        return base

    def save(self, delete_zip_import=True, *args, **kwargs):
        """
        If a zip file is uploaded, extract any images from it and add
        them to the gallery, before removing the zip file.

        Enforces zip-bomb limits (file count, per-entry size, total
        uncompressed size) and rejects zip-slip paths.
        """
        super().save(*args, **kwargs)
        if not self.zip_import:
            return
        max_files, max_total, max_entry = self._zip_limits()
        try:
            zip_file = ZipFile(self.zip_import)
        except BadZipFile as exc:
            raise ValidationError(
                gettext("Invalid or corrupted zip file.")
            ) from exc

        try:
            infos = [i for i in zip_file.infolist() if not i.is_dir()]
            if len(infos) > max_files:
                raise ValidationError(
                    gettext(
                        "Zip contains too many files (%(count)s > %(max)s)."
                    )
                    % {"count": len(infos), "max": max_files}
                )
            total_declared = sum(max(i.file_size, 0) for i in infos)
            if total_declared > max_total:
                raise ValidationError(
                    gettext(
                        "Zip uncompressed size too large "
                        "(%(size)s bytes > %(max)s)."
                    )
                    % {"size": total_declared, "max": max_total}
                )

            imported = 0
            total_read = 0
            for info in infos:
                if info.file_size > max_entry:
                    continue
                base = self._safe_zip_member_name(info.filename)
                if base is None:
                    continue
                # Hard cap remaining budget before read.
                if total_read + info.file_size > max_total:
                    raise ValidationError(
                        gettext("Zip uncompressed size exceeds limit during extract.")
                    )
                try:
                    data = zip_file.read(info)
                except Exception:  # noqa: BLE001 — skip bad members
                    continue
                total_read += len(data)
                if total_read > max_total:
                    raise ValidationError(
                        gettext("Zip uncompressed size exceeds limit during extract.")
                    )
                if len(data) > max_entry:
                    continue
                try:
                    from PIL import Image

                    image = Image.open(BytesIO(data))
                    image.load()
                    image = Image.open(BytesIO(data))
                    image.verify()
                except ImportError:
                    pass
                except Exception:  # noqa: BLE001
                    continue

                tempname = base
                if isinstance(tempname, bytes):
                    encoding = charsetdetect(tempname)["encoding"]
                    tempname = tempname.decode(encoding)

                # A gallery with a slug of "/" tries to extract files
                # to / on disk; see os.path.join docs.
                slug = self.slug if self.slug != "/" else ""
                path = os.path.join(GALLERIES_UPLOAD_DIR, slug, tempname)
                try:
                    saved_path = default_storage.save(path, ContentFile(data))
                except UnicodeEncodeError:
                    from warnings import warn

                    warn(
                        "A file was saved that contains unicode "
                        "characters in its path, but somehow the current "
                        "locale does not support utf-8. You may need to set "
                        "'LC_ALL' to a correct value, eg: 'en_US.UTF-8'."
                    )
                    safe = (
                        tempname.encode("ascii", "ignore").decode("ascii")
                        or "image.bin"
                    )
                    path = os.path.join(GALLERIES_UPLOAD_DIR, slug, safe)
                    saved_path = default_storage.save(path, ContentFile(data))
                self.images.create(file=saved_path)
                imported += 1
                if imported >= max_files:
                    break
        finally:
            zip_file.close()
            if delete_zip_import:
                self.zip_import.delete(save=True)

class Gallery(Page, DocumentBody, RichText, BaseGallery):
    """
    Page bucket for gallery photos with Y1.5 JSON ``body``.
    """

    class Meta:
        verbose_name = _("Gallery")
        verbose_name_plural = _("Galleries")

class GalleryImage(Orderable):

    gallery = models.ForeignKey(
        "Gallery", on_delete=models.CASCADE, related_name="images"
    )
    file = FileField(
        _("File"),
        max_length=200,
        format="Image",
        upload_to=upload_to("galleries.GalleryImage.file", "galleries"),
    )
    description = models.CharField(_("Description"), max_length=1000, blank=True)

    class Meta:
        verbose_name = _("Image")
        verbose_name_plural = _("Images")

    def __str__(self):
        return self.description

    def save(self, *args, **kwargs):
        """
        If no description is given when created, create one from the
        file name.
        """
        if not self.id and not self.description:
            name = force_str(self.file)
            name = name.rsplit("/", 1)[-1].rsplit(".", 1)[0]
            name = name.replace("'", "")
            name = "".join(c if c not in punctuation else " " for c in name)
            # str.title() doesn't deal with unicode very well.
            # http://bugs.python.org/issue6412
            name = "".join(
                s.upper() if i == 0 or name[i - 1] == " " else s
                for i, s in enumerate(name)
            )
            self.description = name
        super().save(*args, **kwargs)
