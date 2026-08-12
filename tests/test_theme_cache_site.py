"""PR-047 / S3: active_theme_template_dir is site-keyed."""

import pytest
from django.contrib.sites.models import Site

from mezzanine.conf.models import Setting
from mezzanine.kits.theme import (
    _active_theme_template_dir_for_site,
    active_theme_template_dir,
    theme_template_dir,
)
from mezzanine.utils.sites import current_site_id, override_current_site_id

pytestmark = pytest.mark.django_db


def test_template_dir_cache_is_per_site():
    site_a = Site.objects.get(pk=current_site_id())
    site_b = Site.objects.create(domain="other-theme.example.com", name="Other")

    Setting._base_manager.update_or_create(
        site_id=site_a.id,
        name="ACTIVE_THEME",
        defaults={"value": "whitehouse"},
    )
    Setting._base_manager.update_or_create(
        site_id=site_b.id,
        name="ACTIVE_THEME",
        defaults={"value": "spotify"},
    )
    _active_theme_template_dir_for_site.cache_clear()

    path_a = _active_theme_template_dir_for_site(site_a.id)
    path_b = _active_theme_template_dir_for_site(site_b.id)
    assert path_a == str(theme_template_dir("whitehouse"))
    assert path_b == str(theme_template_dir("spotify"))
    assert path_a != path_b

    # Ambient current site still resolves correctly.
    with override_current_site_id(site_a.id):
        assert active_theme_template_dir() == path_a
    with override_current_site_id(site_b.id):
        assert active_theme_template_dir() == path_b


def test_set_active_theme_clears_site_cache():
    from mezzanine.kits.theme import set_active_theme

    site_id = current_site_id()
    set_active_theme("whitehouse")
    assert _active_theme_template_dir_for_site(site_id) == str(
        theme_template_dir("whitehouse")
    )
    set_active_theme("time")
    assert _active_theme_template_dir_for_site(site_id) == str(
        theme_template_dir("time")
    )
