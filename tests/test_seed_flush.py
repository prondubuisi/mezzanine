"""PR-044: seed --flush clears categories/keywords; Setting uniqueness (B4/B8/B9)."""

import pytest
from django.contrib.sites.models import Site
from django.core.management import call_command
from django.db import IntegrityError

from mezzanine.blog.models import BlogCategory, BlogPost
from mezzanine.conf.models import Setting
from mezzanine.core.models import CONTENT_STATUS_PUBLISHED
from mezzanine.utils.sites import current_site_id
from tests.factories import SuperUserFactory

pytestmark = pytest.mark.django_db


def test_seed_flush_clears_categories_from_prior_profile():
    SuperUserFactory(username="admin", email="a@example.com")
    call_command("seed_site_clone", site="techcrunch", flush=True, verbosity=0)
    assert BlogCategory.objects.filter(slug="venture").exists()
    assert BlogCategory.objects.count() >= 1

    call_command("seed_site_clone", site="time", flush=True, verbosity=0)
    # TIME profile categories replace TechCrunch ones — no orphan venture cat.
    assert not BlogCategory.objects.filter(slug="venture").exists()
    assert BlogCategory.objects.filter(slug="politics").exists()
    assert (
        BlogPost.objects.filter(status=CONTENT_STATUS_PUBLISHED).count() >= 1
    )


def test_setting_site_name_unique():
    site_id = current_site_id()
    site = Site.objects.get(pk=site_id)
    Setting.objects.create(name="SITE_TITLE", value="One", site=site)
    with pytest.raises(IntegrityError):
        Setting.objects.create(name="SITE_TITLE", value="Two", site=site)
