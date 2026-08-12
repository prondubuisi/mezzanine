import io
import os
import zipfile
from shutil import rmtree
from uuid import uuid4

from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.test import override_settings

from mezzanine.conf import settings
from mezzanine.core.templatetags.mezzanine_tags import thumbnail
from mezzanine.galleries.models import GALLERIES_UPLOAD_DIR, BaseGallery, Gallery
from mezzanine.utils.tests import TestCase, copy_test_to_media


class GalleriesTests(TestCase):
    def test_gallery_import(self):
        """
        Test that a gallery creates images when given a zip file to
        import, and that descriptions are created.
        """
        zip_name = "gallery.zip"
        copy_test_to_media("mezzanine.core", zip_name)
        title = str(uuid4())
        gallery = Gallery.objects.create(title=title, zip_import=zip_name)
        images = list(gallery.images.all())
        self.assertTrue(images)
        self.assertTrue(all([image.description for image in images]))
        # Clean up.
        rmtree(os.path.join(settings.MEDIA_ROOT, GALLERIES_UPLOAD_DIR, title))

    def test_zip_slip_paths_rejected(self):
        """Zip members with .. or absolute paths are not extracted."""
        self.assertIsNone(BaseGallery._safe_zip_member_name("../etc/passwd"))
        self.assertIsNone(BaseGallery._safe_zip_member_name("/abs/evil.jpg"))
        self.assertIsNone(BaseGallery._safe_zip_member_name("a/../../b.jpg"))
        self.assertEqual(BaseGallery._safe_zip_member_name("ok/photo.jpg"), "photo.jpg")

    @override_settings(GALLERIES_ZIP_MAX_FILES=1)
    def test_zip_max_files_limit(self):
        """Zip with more members than GALLERIES_ZIP_MAX_FILES is rejected."""
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            # Minimal JPEG-like payloads; PIL may reject — still counts as files.
            zf.writestr("a.jpg", b"\xff\xd8\xff\xd9")
            zf.writestr("b.jpg", b"\xff\xd8\xff\xd9")
        buf.seek(0)
        title = str(uuid4())
        gallery = Gallery(title=title)
        gallery.zip_import.save("too-many.zip", ContentFile(buf.read()), save=False)
        with self.assertRaises(ValidationError):
            gallery.save()

    def test_thumbnail_generation(self):
        """
        Test that a thumbnail is created and resized.
        """
        try:
            from PIL import Image
        except ImportError:
            return
        image_name = "image.jpg"
        size = (24, 24)
        copy_test_to_media("mezzanine.core", image_name)
        thumb_name = os.path.join(
            settings.THUMBNAILS_DIR_NAME,
            image_name,
            image_name.replace(".", "-%sx%s." % size),
        )
        thumb_path = os.path.join(settings.MEDIA_ROOT, thumb_name)
        thumb_image = thumbnail(image_name, *size)
        self.assertEqual(os.path.normpath(thumb_image.lstrip("/")), thumb_name)
        self.assertNotEqual(os.path.getsize(thumb_path), 0)
        thumb = Image.open(thumb_path)
        self.assertEqual(thumb.size, size)
        # Clean up.
        del thumb
        os.remove(os.path.join(settings.MEDIA_ROOT, image_name))
        os.remove(os.path.join(thumb_path))
        rmtree(os.path.join(os.path.dirname(thumb_path)))
