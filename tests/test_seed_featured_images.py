"""Featured image placeholders on seed_site_clone (parity S5)."""

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command

from mezzanine.blog.models import BlogPost
from mezzanine.demos.seed_images import placeholder_png
from mezzanine.kits.loader import apply_kit

User = get_user_model()


def test_placeholder_png_is_valid_png():
    data = placeholder_png("series-a-vertical-saas")
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
    assert len(data) > 200
    # Stable for same slug
    assert placeholder_png("series-a-vertical-saas") == data


def test_editorial_kit_enables_featured_image_setting(tmp_path):
    project = tmp_path / "site"
    app = "mysite"
    (project / app).mkdir(parents=True)
    (project / app / "settings.py").write_text(
        "INSTALLED_APPS = [\n"
        '    "django.contrib.admin",\n'
        '    "mezzanine.core",\n'
        '    "mezzanine.pages",\n'
        "]\n"
        'STATIC_ROOT = os.path.join(PROJECT_ROOT, STATIC_URL.strip("/"))\n',
        encoding="utf-8",
    )
    apply_kit("techcrunch", project, app)
    settings = (project / app / "settings.py").read_text(encoding="utf-8")
    assert "BLOG_USE_FEATURED_IMAGE = True" in settings


@pytest.mark.django_db
def test_seed_attaches_featured_images():
    User.objects.create_superuser("admin", "a@example.com", "passwordpassword")
    call_command("seed_site_clone", site="techcrunch", flush=True, verbosity=0)
    posts = BlogPost.objects.all()
    assert posts.count() >= 4
    with_image = [p for p in posts if p.featured_image]
    assert len(with_image) == posts.count()
    # Path under blog/seed/
    assert "blog/seed/" in str(with_image[0].featured_image)
