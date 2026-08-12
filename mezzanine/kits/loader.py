"""Load and validate unsigned site kits (design §6.1)."""

from __future__ import annotations

import importlib.util
import json
import re
import shutil
from pathlib import Path

import mezzanine

# Types declared in kit.json map to concrete models under mezzanine.*.
_TYPE_IMPORTS = {
    "pages.RichTextPage": "mezzanine.pages.models.RichTextPage",
    "pages.Link": "mezzanine.pages.models.Link",
    "forms.Form": "mezzanine.forms.models.Form",
    "blog.BlogPost": "mezzanine.blog.models.BlogPost",
    "galleries.Gallery": "mezzanine.galleries.models.Gallery",
}


class KitError(Exception):
    """Raised when a kit is missing or fails validation."""


def kit_path(name: str) -> Path:
    if not re.fullmatch(r"[\w-]+", name or ""):
        raise KitError("Invalid kit name %r" % name)
    root = Path(mezzanine.__path__[0]) / "kits" / name
    kits_root = (Path(mezzanine.__path__[0]) / "kits").resolve()
    if not root.resolve().is_relative_to(kits_root):
        raise KitError("Invalid kit name %r" % name)
    return root


def load_kit_meta(name: str) -> tuple[Path, dict]:
    root = kit_path(name)
    meta_path = root / "kit.json"
    if not root.is_dir() or not meta_path.is_file():
        raise KitError("Unknown kit %r (no kit.json under mezzanine/kits/)." % name)
    try:
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise KitError("Invalid kit.json for %r: %s" % (name, exc)) from exc
    if not isinstance(meta, dict):
        raise KitError("kit.json for %r must be a JSON object." % name)
    return root, meta


def _parse_version(version: str) -> tuple[int, ...]:
    match = re.match(r"(\d+)(?:\.(\d+))?(?:\.(\d+))?", version)
    if not match:
        return (0,)
    return tuple(int(part or 0) for part in match.groups())


def _compat_ok(spec: str, version: str) -> bool:
    """
    Minimal ``nova_compat`` checker for specs like ``>=0.1,<2``.

    Development trees ship ``9999dev0`` and always pass (A0′).
    """
    if version.startswith("9999"):
        return True
    ver = _parse_version(version)
    for clause in (part.strip() for part in spec.split(",")):
        if not clause:
            continue
        op_match = re.match(r"^(>=|<=|>|<|==)(.+)$", clause)
        if not op_match:
            raise KitError("Unsupported nova_compat clause %r" % clause)
        op, raw = op_match.group(1), op_match.group(2).strip()
        bound = _parse_version(raw)
        if op == ">=" and not ver >= bound:
            return False
        if op == "<=" and not ver <= bound:
            return False
        if op == ">" and not ver > bound:
            return False
        if op == "<" and not ver < bound:
            return False
        if op == "==" and ver != bound:
            return False
    return True


def validate_kit(meta: dict, *, version: str | None = None) -> None:
    name = meta.get("name")
    if not name:
        raise KitError("kit.json missing required field 'name'")
    if "signature" in meta:
        raise KitError(
            "kit %r declares a signature; Y1 kits are unsigned (design §6.1)." % name
        )
    compat = meta.get("nova_compat")
    if not compat:
        raise KitError("kit %r missing nova_compat" % name)
    current = version if version is not None else mezzanine.__version__
    if not _compat_ok(str(compat), current):
        raise KitError(
            "kit %r requires nova_compat %s; running %s" % (name, compat, current)
        )
    types = meta.get("types") or []
    if not isinstance(types, list):
        raise KitError("kit %r types must be a list" % name)
    for type_name in types:
        dotted = _TYPE_IMPORTS.get(type_name)
        if dotted is None:
            # Fall back: pages.RichTextPage → mezzanine.pages.models.RichTextPage
            if "." not in type_name:
                raise KitError("kit %r unknown type %r" % (name, type_name))
            app_label, model_name = type_name.split(".", 1)
            dotted = "mezzanine.%s.models.%s" % (app_label, model_name)
        module_path, _, attr = dotted.rpartition(".")
        # Avoid import_module: models need a configured Django app registry.
        # nova-project only configures mezzanine.bin when this runs.
        spec = importlib.util.find_spec(module_path)
        if spec is None or not spec.origin:
            raise KitError(
                "kit %r type %r is not installed (no module %s)"
                % (name, type_name, module_path)
            )
        source = Path(spec.origin).read_text(encoding="utf-8")
        if not re.search(r"class\s+%s\b" % re.escape(attr), source):
            raise KitError(
                "kit %r type %r is not installed (no class %s)"
                % (name, type_name, attr)
            )


def apply_kit(name: str, project_dir: str | Path, project_app: str) -> dict:
    """
    Overlay a kit onto a project written by nova-project.

    - validates kit.json
    - copies templates/ and static/ into the project
    - rewrites INSTALLED_APPS for brochure (no blog/galleries)
    """
    root, meta = load_kit_meta(name)
    validate_kit(meta)
    project_dir = Path(project_dir)
    project_app_dir = project_dir / project_app

    # Settings first so a rewrite failure does not leave kit templates alone.
    if name == "brochure":
        _apply_brochure_settings(project_app_dir)

    templates_src = root / "templates"
    if templates_src.is_dir():
        dest = project_dir / "templates"
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(templates_src, dest)

    static_src = root / "static"
    if static_src.is_dir():
        dest = project_dir / "static"
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(static_src, dest)

    (project_dir / ".nova-kit").write_text(name + "\n", encoding="utf-8")
    return meta


def _apply_brochure_settings(project_app_dir: Path) -> None:
    settings_path = project_app_dir / "settings.py"
    text = settings_path.read_text(encoding="utf-8")
    brochure_apps = """INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.redirects",
    "django.contrib.sessions",
    "django.contrib.sites",
    "django.contrib.sitemaps",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "mezzanine.kits.brochure",
    "mezzanine.boot",
    "mezzanine.conf",
    "mezzanine.core",
    "mezzanine.generic",
    "mezzanine.pages",
    "mezzanine.forms",
    "mezzanine.migrate",
]
"""
    new_text, n = re.subn(
        r"INSTALLED_APPS\s*=\s*\[[^\]]*\]",
        brochure_apps.rstrip(),
        text,
        count=1,
        flags=re.S,
    )
    if n != 1:
        raise KitError("Could not rewrite INSTALLED_APPS for brochure kit")
    # Project templates dir is already in TEMPLATES DIRS; ensure static dir.
    if "STATICFILES_DIRS" not in new_text:
        new_text = new_text.replace(
            "STATIC_ROOT = os.path.join(PROJECT_ROOT, STATIC_URL.strip(\"/\"))",
            "STATIC_ROOT = os.path.join(PROJECT_ROOT, STATIC_URL.strip(\"/\"))\n"
            "STATICFILES_DIRS = [os.path.join(PROJECT_ROOT, \"static\")]",
            1,
        )
    settings_path.write_text(new_text, encoding="utf-8")
