"""PR-061 / PR-062 — KitRegistry gate + marketplace activate (KD21).

DESIGN.md Amendment 4 §A4.3: every ACTIVE_THEME path checks the registry;
unlisted kits are blocked.
"""

import pytest
from django.test import Client
from django.urls import reverse

from mezzanine.kits.registry import (
    RegistryError,
    assert_kit_activatable,
    get_registry_entry,
    is_kit_registered,
    list_registry_entries,
)
from mezzanine.kits.theme import ThemeError, set_active_theme
from tests.factories import SuperUserFactory

pytestmark = pytest.mark.django_db


def test_first_party_kits_are_registered():
    names = {e["name"] for e in list_registry_entries()}
    for required in (
        "brochure",
        "whitehouse",
        "spotify",
        "techcrunch",
        "time",
        "magazine",
        "institute",
        "wporg",
    ):
        assert required in names
        assert is_kit_registered(required)
        entry = assert_kit_activatable(required)
        assert entry["trusted"] is True


def test_unknown_kit_blocked():
    assert not is_kit_registered("shadow-kit")
    with pytest.raises(RegistryError, match="not in KitRegistry"):
        assert_kit_activatable("shadow-kit")


def test_set_active_theme_rejects_unregistered():
    with pytest.raises(RegistryError, match="not in KitRegistry"):
        set_active_theme("shadow-kit")


def test_set_active_theme_whitehouse_still_works():
    meta = set_active_theme("whitehouse")
    assert meta["name"] == "whitehouse"


def test_marketplace_requires_staff():
    client = Client()
    resp = client.get("/_nova/marketplace/")
    # unauthenticated → 404 or redirect (staff gate)
    assert resp.status_code in (302, 403, 404)


def test_marketplace_lists_registry_for_superuser():
    user = SuperUserFactory()
    client = Client()
    client.force_login(user)
    resp = client.get("/_nova/marketplace/")
    assert resp.status_code == 200
    body = resp.content.decode("utf-8")
    assert "whitehouse" in body
    assert "spotify" in body
    assert "Kit marketplace" in body or "marketplace" in body.lower()


def test_marketplace_activate_post():
    user = SuperUserFactory()
    client = Client()
    client.force_login(user)
    resp = client.post("/_nova/marketplace/activate/", {"kit": "whitehouse"})
    assert resp.status_code == 302
    assert resp.url == "/_nova/marketplace/"
    from mezzanine.conf.models import Setting

    row = Setting.objects.filter(name="ACTIVE_THEME").first()
    assert row is not None
    assert row.value == "whitehouse"


def test_marketplace_activate_blocks_shadow():
    user = SuperUserFactory()
    client = Client()
    client.force_login(user)
    resp = client.post("/_nova/marketplace/activate/", {"kit": "shadow-kit"})
    assert resp.status_code == 302
    # Should not create ACTIVE_THEME=shadow-kit
    from mezzanine.conf.models import Setting

    row = Setting.objects.filter(name="ACTIVE_THEME", value="shadow-kit").first()
    assert row is None
