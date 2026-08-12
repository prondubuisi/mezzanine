"""
KitRegistry — curated kit marketplace manifest (KD21 / PR-061).

Y1 ships an in-repo JSON file (unsigned first-party kits listed as trusted).
Activation must call ``assert_kit_activatable`` before wiring plugins or
persisting ``ACTIVE_THEME``. Cryptographic ed25519 verification is reserved
for a later turn (OQ5); until then, "signature" null + trusted=true means
human-curated in this file.
"""

from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

import mezzanine
from mezzanine.kits.loader import KitError


class RegistryError(KitError):
    """Kit not in registry or failed activation policy."""


def registry_path() -> Path:
    return Path(mezzanine.__path__[0]) / "kits" / "registry.json"


@lru_cache(maxsize=1)
def load_registry() -> dict[str, Any]:
    path = registry_path()
    if not path.is_file():
        raise RegistryError("KitRegistry missing at %s" % path)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise RegistryError("Invalid registry.json: %s" % exc) from exc
    if not isinstance(data, dict) or not isinstance(data.get("kits"), list):
        raise RegistryError("registry.json must be an object with a kits list")
    return data


def clear_registry_cache() -> None:
    load_registry.cache_clear()


def list_registry_entries() -> list[dict[str, Any]]:
    """Return kit entries from the registry (copy-ish list of dicts)."""
    return list(load_registry().get("kits") or [])


def get_registry_entry(name: str) -> dict[str, Any] | None:
    if not name or not re.fullmatch(r"[\w-]+", name):
        return None
    for entry in list_registry_entries():
        if entry.get("name") == name:
            return entry
    return None


def is_kit_registered(name: str) -> bool:
    return get_registry_entry(name) is not None


def assert_kit_activatable(name: str) -> dict[str, Any]:
    """
    Gate for every ACTIVE_THEME write path (PR-061).

    Raises RegistryError when the kit is absent from KitRegistry or not
    marked trusted. Returns the registry entry on success.
    """
    if not name or not re.fullmatch(r"[\w-]+", name):
        raise RegistryError("Invalid kit name %r" % name)
    entry = get_registry_entry(name)
    if entry is None:
        raise RegistryError(
            "Activation blocked — kit %r is not in KitRegistry (unsigned / "
            "unreviewed). Add it to mezzanine/kits/registry.json after human "
            "review (KD21)." % name
        )
    if entry.get("trusted") is not True and not entry.get("signature"):
        raise RegistryError(
            "Activation blocked — kit %r is listed but not trusted and has no "
            "signature." % name
        )
    # Future: verify ed25519 signature over bundle hash when signature is set.
    return entry
