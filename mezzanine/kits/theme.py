"""
WordPress-like theme package contract for first-party kits.

A kit may ship ``theme.json`` (preferred) or declare theme fields on
``kit.json``. Runtime selection uses the ``ACTIVE_THEME`` setting; the
active theme's package templates load *before* project copy-on-create
templates so chrome can switch without re-running nova-project.
"""

from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

import mezzanine
from mezzanine.kits.loader import KitError, kit_path, load_kit_meta


# Required / optional keys for theme.json (lean WP theme.json analogue).
_REQUIRED = ("name", "version")
_OPTIONAL = (
    "description",
    "slots",
    "menus",
    "colors",
    "tokens",
    "plugins",
    "template_package",
    "screenshot",
)


class ThemeError(KitError):
    """Theme package missing or invalid."""


def kits_root() -> Path:
    return Path(mezzanine.__path__[0]) / "kits"


def theme_json_path(name: str) -> Path:
    root = kit_path(name)
    preferred = root / "theme.json"
    if preferred.is_file():
        return preferred
    # Fallback: kit.json may embed theme fields (name/version/slots/colors).
    return root / "kit.json"


def load_theme_meta(name: str) -> dict[str, Any]:
    """Load and validate theme metadata for a kit name."""
    path = theme_json_path(name)
    if not path.is_file():
        raise ThemeError("No theme.json or kit.json for theme %r" % name)
    try:
        meta = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ThemeError("Invalid theme metadata for %r: %s" % (name, exc)) from exc
    if not isinstance(meta, dict):
        raise ThemeError("theme metadata for %r must be a JSON object" % name)
    # If loading kit.json, require it to look like a theme (tokens or slots or kind).
    if path.name == "kit.json":
        if not (
            meta.get("tokens")
            or meta.get("slots")
            or meta.get("kind") == "theme"
            or meta.get("colors")
        ):
            raise ThemeError(
                "kit.json for %r has no theme fields (tokens/slots/colors/kind)" % name
            )
    for key in _REQUIRED:
        if not meta.get(key):
            # kit.json always has name; version may be present
            if key == "name" and meta.get("name"):
                continue
            if key == "version" and meta.get("version"):
                continue
            if key not in meta:
                # version optional when falling back to kit only if name exists
                if key == "version":
                    meta = {**meta, "version": meta.get("version") or "0.0.0"}
                    continue
                raise ThemeError("theme %r missing required field %r" % (name, key))
    if meta.get("name") and meta["name"] != name:
        # Allow theme.json name to match kit folder
        if meta["name"] != name:
            pass  # folder name is canonical for loading
    return meta


def list_theme_names() -> list[str]:
    """First-party kits that expose a theme package."""
    names = []
    root = kits_root()
    if not root.is_dir():
        return names
    for child in sorted(root.iterdir()):
        if not child.is_dir() or child.name in ("shared", "__pycache__"):
            continue
        if not re.fullmatch(r"[\w-]+", child.name):
            continue
        if (child / "theme.json").is_file():
            names.append(child.name)
            continue
        kit_json = child / "kit.json"
        if kit_json.is_file():
            try:
                meta = json.loads(kit_json.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                continue
            if meta.get("tokens") or meta.get("slots") or meta.get("kind") == "theme":
                names.append(child.name)
    return names


def theme_package(name: str) -> str:
    """Dotted import path for the theme Django app."""
    return "mezzanine.kits.%s" % name


def theme_template_dir(name: str) -> Path | None:
    """Absolute path to the theme package templates/ directory."""
    try:
        root = kit_path(name)
    except KitError:
        return None
    templates = root / "templates"
    return templates if templates.is_dir() else None


def theme_plugins(meta: dict[str, Any]) -> list[str]:
    plugins = []
    for p in meta.get("plugins") or []:
        p = str(p).strip()
        if p and p not in plugins:
            plugins.append(p)
    return plugins


def theme_plugins_installed(meta: dict[str, Any]) -> bool:
    from django.conf import settings

    installed = set(settings.INSTALLED_APPS)
    return all(p in installed for p in theme_plugins(meta))


def get_active_theme_name() -> str:
    """
    Resolve ACTIVE_THEME from Mezzanine settings (DB Setting or settings.py).
    Empty string means no runtime theme override.
    """
    try:
        from mezzanine.conf import settings as msettings

        name = getattr(msettings, "ACTIVE_THEME", "") or ""
    except Exception:  # noqa: BLE001
        return ""
    return str(name).strip()


def set_active_theme(name: str) -> dict[str, Any]:
    """
    Persist ACTIVE_THEME via conf.Setting and validate the package.
    Returns theme metadata.
    """
    if not name:
        raise ThemeError("Theme name is required")
    meta = load_theme_meta(name)
    if not theme_plugins_installed(meta):
        missing = [
            p
            for p in theme_plugins(meta)
            if p
            not in __import__("django.conf", fromlist=["settings"]).settings.INSTALLED_APPS
        ]
        raise ThemeError(
            "Theme %r requires plugins not in INSTALLED_APPS: %s"
            % (name, ", ".join(missing))
        )
    from mezzanine.conf import settings as msettings
    from mezzanine.conf.models import Setting

    Setting.objects.update_or_create(
        name="ACTIVE_THEME",
        defaults={"value": name},
    )
    if hasattr(msettings, "clear_cache"):
        msettings.clear_cache()
    elif hasattr(msettings, "_loaded"):
        msettings._loaded = False
    active_theme_template_dir.cache_clear()
    return meta


@lru_cache(maxsize=8)
def active_theme_template_dir() -> str:
    """Filesystem path for the active theme templates (empty if none)."""
    name = get_active_theme_name()
    if not name:
        return ""
    path = theme_template_dir(name)
    return str(path) if path else ""


def profile_theme_map() -> dict[str, str]:
    """Map demo site profile slugs → theme kit names (when one exists)."""
    return {
        "whitehouse": "whitehouse",
        # Listening CMS demo uses music seed, not newsroom profile.
        "spotify_listen": "spotify",
    }
