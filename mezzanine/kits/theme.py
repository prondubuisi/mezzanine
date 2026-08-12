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
from mezzanine.kits.loader import KitError, kit_path

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


# Theme customizer color values (DESIGN.md Amendment 3 S1 / PR-045).
# Only hex CSS colors are accepted — never free-form strings into |safe CSS.
_HEX_COLOR_RE = re.compile(
    r"^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{4}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})$"
)
_CSS_COLOR_KEYWORDS = frozenset(
    {
        "transparent",
        "currentcolor",
        "black",
        "white",
        "red",
        "green",
        "blue",
        "yellow",
        "orange",
        "purple",
        "gray",
        "grey",
        "silver",
        "navy",
        "teal",
        "maroon",
        "olive",
        "lime",
        "aqua",
        "fuchsia",
    }
)


def normalize_theme_color(value: str | None) -> str | None:
    """
    Return a safe CSS color string, empty string to clear, or None if invalid.

    Accepts ``#rgb`` / ``#rrggbb`` / ``#rgba`` / ``#rrggbbaa`` (case-insensitive)
    and a small fixed keyword allowlist. Rejects everything else so values
    never become a stored-XSS vector via ``theme_customizer_css``.
    """
    if value is None:
        return None
    val = str(value).strip()
    if not val:
        return ""
    if len(val) > 64:
        return None
    if _HEX_COLOR_RE.match(val):
        return val.lower()
    lower = val.lower()
    if lower in _CSS_COLOR_KEYWORDS:
        return lower
    return None


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


def set_active_theme(
    name: str, *, project_root: str | Path | None = None
) -> dict[str, Any]:
    """
    Persist ACTIVE_THEME via conf.Setting and validate the package.
    Also writes ``.nova-theme`` so the next process start can auto-load plugins.
    Returns theme metadata.
    """
    if not name:
        raise ThemeError("Theme name is required")
    meta = load_theme_meta(name)
    missing = missing_theme_plugins(meta)
    if missing:
        # Try importability first (may already be on path but not installed).
        unimportable = []
        for p in missing:
            try:
                __import__(p)
            except ImportError:
                unimportable.append(p)
        if unimportable:
            raise ThemeError(
                "Theme %r requires plugins that are not installed/importable: %s. "
                "Add them to INSTALLED_APPS (or re-run with kit that includes them) "
                "and restart."
                % (name, ", ".join(unimportable))
            )
        # Importable but not in INSTALLED_APPS — activate still records theme;
        # conf will append on next process boot via .nova-theme.
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
    write_nova_theme_marker(name, project_root=project_root)
    active_theme_template_dir.cache_clear()
    return meta


def missing_theme_plugins(meta: dict[str, Any]) -> list[str]:
    from django.conf import settings

    installed = set(settings.INSTALLED_APPS)
    return [p for p in theme_plugins(meta) if p not in installed]


def write_nova_theme_marker(
    name: str, *, project_root: str | Path | None = None
) -> Path | None:
    """
    Persist active theme name for process startup (plugin auto-append).

    Written next to manage.py when project_root is known; also under cwd.
    """
    roots: list[Path] = []
    if project_root:
        roots.append(Path(project_root))
    try:
        from django.conf import settings as dj

        if getattr(dj, "PROJECT_ROOT", None):
            roots.append(Path(dj.PROJECT_ROOT))
    except Exception:  # noqa: BLE001
        pass
    roots.append(Path.cwd())
    written = None
    for root in roots:
        try:
            if not root.is_dir():
                continue
            path = root / ".nova-theme"
            path.write_text(name.strip() + "\n", encoding="utf-8")
            written = path
            break
        except OSError:
            continue
    return written


def read_nova_theme_marker(project_root: str | Path | None = None) -> str:
    candidates: list[Path] = []
    if project_root:
        candidates.append(Path(project_root) / ".nova-theme")
    try:
        from django.conf import settings as dj

        if getattr(dj, "PROJECT_ROOT", None):
            candidates.append(Path(dj.PROJECT_ROOT) / ".nova-theme")
    except Exception:  # noqa: BLE001
        pass
    candidates.append(Path.cwd() / ".nova-theme")
    for path in candidates:
        try:
            if path.is_file():
                return path.read_text(encoding="utf-8").strip().splitlines()[0].strip()
        except OSError:
            continue
    return ""


def resolve_slot_template(slot: str, fallback: str) -> str:
    """
    WordPress-style template hierarchy step: active theme slot → fallback.

    ``theme.json`` slots map logical names (home, single, chrome, …) to
    template paths relative to the theme package templates/ dir.
    """
    name = get_active_theme_name()
    if not name:
        return fallback
    try:
        meta = load_theme_meta(name)
    except ThemeError:
        return fallback
    slots = meta.get("slots") or {}
    candidate = slots.get(slot)
    if not candidate:
        return fallback
    # Prefer theme package file if it exists; else fall back.
    tdir = theme_template_dir(name)
    if tdir and (tdir / candidate).is_file():
        return str(candidate)
    return fallback


def get_theme_colors() -> dict[str, str]:
    """
    Colors for Customizer: theme.json defaults merged with Setting overrides.

    Keys: ink, accent, accent_ink, canvas, paper (subset may be present).
    """
    colors: dict[str, str] = {}
    name = get_active_theme_name()
    if name:
        try:
            meta = load_theme_meta(name)
            raw = meta.get("colors") or {}
            if isinstance(raw, dict):
                colors.update({str(k): str(v) for k, v in raw.items() if v})
        except ThemeError:
            pass
    # Overrides from editable settings
    try:
        from mezzanine.conf import settings as msettings

        mapping = {
            "ink": "THEME_COLOR_INK",
            "accent": "THEME_COLOR_ACCENT",
            "accent_ink": "THEME_COLOR_ACCENT_INK",
            "canvas": "THEME_COLOR_CANVAS",
            "paper": "THEME_COLOR_PAPER",
        }
        for key, setting_name in mapping.items():
            val = getattr(msettings, setting_name, "") or ""
            safe = normalize_theme_color(str(val).strip())
            if safe:
                colors[key] = safe
    except Exception:  # noqa: BLE001
        pass
    return colors


def get_theme_logo_url() -> str:
    try:
        from mezzanine.conf import settings as msettings

        return str(getattr(msettings, "THEME_LOGO_URL", "") or "").strip()
    except Exception:  # noqa: BLE001
        return ""


def theme_customizer_css() -> str:
    """
    Inline CSS variable overrides for active theme colors.

    Only normalized (hex/keyword) colors are emitted — defense in depth
    for values that may predate PR-045 validation (S1).
    """
    colors = get_theme_colors()
    if not colors:
        return ""
    # Map theme.json keys → CSS custom properties used by kits.
    var_map = {
        "ink": "--nova-ink",
        "accent": "--nova-accent",
        "accent_ink": "--nova-accent-ink",
        "canvas": "--nova-canvas",
        "paper": "--nova-paper",
        # Spotify player tokens
        "sp_bg": "--sp-bg",
        "sp_accent": "--sp-accent",
        "sp_surface": "--sp-surface",
    }
    lines = []
    safe_colors: dict[str, str] = {}
    for key, raw in colors.items():
        safe = normalize_theme_color(raw)
        if safe:
            safe_colors[key] = safe
    for key, css_var in var_map.items():
        if key in safe_colors:
            lines.append("%s: %s;" % (css_var, safe_colors[key]))
    # Also mirror accent/ink onto Spotify vars when present.
    if "accent" in safe_colors and "sp_accent" not in safe_colors:
        lines.append("--sp-accent: %s;" % safe_colors["accent"])
    if "ink" in safe_colors and "sp_surface" not in safe_colors:
        lines.append("--sp-surface: %s;" % safe_colors["ink"])
    if "canvas" in safe_colors and "sp_bg" not in safe_colors:
        lines.append("--sp-bg: %s;" % safe_colors["canvas"])
    if not lines:
        return ""
    return ":root {\n  " + "\n  ".join(lines) + "\n}\n"


def set_theme_customizer(
    *,
    colors: dict[str, str] | None = None,
    logo_url: str | None = None,
) -> None:
    """Persist customizer fields to conf.Setting rows."""
    from mezzanine.conf import settings as msettings
    from mezzanine.conf.models import Setting

    color_settings = {
        "ink": "THEME_COLOR_INK",
        "accent": "THEME_COLOR_ACCENT",
        "accent_ink": "THEME_COLOR_ACCENT_INK",
        "canvas": "THEME_COLOR_CANVAS",
        "paper": "THEME_COLOR_PAPER",
    }
    if colors:
        for key, setting_name in color_settings.items():
            if key not in colors:
                continue
            safe = normalize_theme_color(colors[key])
            if safe is None:
                # Reject invalid (e.g. XSS payloads); leave prior value alone.
                continue
            if safe:
                Setting.objects.update_or_create(
                    name=setting_name, defaults={"value": safe}
                )
            else:
                Setting.objects.filter(name=setting_name).delete()
    if logo_url is not None:
        logo = str(logo_url).strip()
        if logo:
            Setting.objects.update_or_create(
                name="THEME_LOGO_URL", defaults={"value": logo[:500]}
            )
        else:
            Setting.objects.filter(name="THEME_LOGO_URL").delete()
    if hasattr(msettings, "clear_cache"):
        msettings.clear_cache()
    elif hasattr(msettings, "_loaded"):
        msettings._loaded = False


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
        "techcrunch": "techcrunch",
        "time": "time",
        # Listening CMS demo uses music seed, not newsroom profile.
        "spotify_listen": "spotify",
    }


def apps_for_theme(name: str) -> list[str]:
    """Kit package + theme.json plugins for INSTALLED_APPS wiring."""
    apps = []
    kit = theme_package(name)
    apps.append(kit)
    try:
        meta = load_theme_meta(name)
        apps.extend(theme_plugins(meta))
    except ThemeError:
        pass
    # de-dupe preserve order
    out = []
    for a in apps:
        if a not in out:
            out.append(a)
    return out
