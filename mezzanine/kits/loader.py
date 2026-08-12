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
    "music.Artist": "mezzanine.music.models.Artist",
    "music.Album": "mezzanine.music.models.Album",
    "music.Track": "mezzanine.music.models.Track",
    "music.Playlist": "mezzanine.music.models.Playlist",
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


def kit_wants_blog(meta: dict) -> bool:
    """True when kit.json types include blog (editorial / newsroom kits)."""
    types = meta.get("types") or []
    return any(str(t).startswith("blog.") for t in types)


def kit_seed_profile(meta: dict) -> str | None:
    """Optional seed_site_clone profile slug from kit.json."""
    seed = meta.get("seed_profile")
    if seed is None:
        return None
    seed = str(seed).strip()
    return seed or None


def kit_urlconf(meta: dict) -> str | None:
    """Optional dotted urlpatterns module mounted at site root."""
    urlconf = meta.get("urlconf")
    if urlconf is None:
        return None
    urlconf = str(urlconf).strip()
    return urlconf or None


def kit_plugins(meta: dict) -> list[str]:
    """
    Extra Django apps required by the kit (WordPress “plugins”).

    Declared in kit.json as ``plugins``: [\"mezzanine.music\", …].
    Types like ``music.Track`` also imply ``mezzanine.music``.
    """
    plugins: list[str] = []
    for raw in meta.get("plugins") or []:
        p = str(raw).strip()
        if p and p not in plugins:
            plugins.append(p)
    for type_name in meta.get("types") or []:
        if str(type_name).startswith("music."):
            if "mezzanine.music" not in plugins:
                plugins.append("mezzanine.music")
            break
    return plugins


def kit_seed_command(meta: dict) -> str | None:
    """Optional management command name to seed CMS content after createdb."""
    cmd = meta.get("seed_command")
    if cmd is None:
        return None
    cmd = str(cmd).strip()
    return cmd or None


# KD20 / PR-059 — kit fields.json → FieldSchema rows.
_FIELD_TYPES = frozenset(
    {"text", "richtext", "number", "boolean", "choice", "reference"}
)
_NAME_RE = re.compile(r"^[a-z][a-z0-9_]*$")


def fields_json_path(name: str) -> Path:
    """Path to a kit's fields.json (may not exist)."""
    return kit_path(name) / "fields.json"


def load_fields_json(name: str) -> dict | None:
    """
    Load and lightly validate ``fields.json`` for a kit.

    Returns None when the kit has no fields.json (optional). Raises KitError
    on invalid JSON or shape. Same path containment as theme.json (kit_path).
    """
    path = fields_json_path(name)
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise KitError("Invalid fields.json for %r: %s" % (name, exc)) from exc
    if not isinstance(data, dict):
        raise KitError("fields.json for %r must be a JSON object" % name)
    fields = data.get("fields")
    if fields is None:
        raise KitError("fields.json for %r missing 'fields' list" % name)
    if not isinstance(fields, list):
        raise KitError("fields.json for %r 'fields' must be a list" % name)
    for i, entry in enumerate(fields):
        if not isinstance(entry, dict):
            raise KitError(
                "fields.json for %r entry %s must be an object" % (name, i)
            )
        fname = entry.get("name")
        if not fname or not _NAME_RE.match(str(fname)):
            raise KitError(
                "fields.json for %r entry %s has invalid name %r" % (name, i, fname)
            )
        ftype = entry.get("field_type", "text")
        if ftype not in _FIELD_TYPES:
            raise KitError(
                "fields.json for %r field %r has unknown field_type %r"
                % (name, fname, ftype)
            )
        if not entry.get("content_type"):
            raise KitError(
                "fields.json for %r field %r missing content_type" % (name, fname)
            )
        if not entry.get("label"):
            raise KitError(
                "fields.json for %r field %r missing label" % (name, fname)
            )
    return data


def _resolve_content_type(dotted: str):
    """
    Map ``app_label.ModelName`` (or kit type alias) to a ContentType.

    Uses the same type map as kit.json ``types`` where possible.
    """
    from django.apps import apps as django_apps
    from django.contrib.contenttypes.models import ContentType

    dotted = str(dotted).strip()
    if dotted in _TYPE_IMPORTS:
        module_path = _TYPE_IMPORTS[dotted]
        # mezzanine.pages.models.RichTextPage → pages, RichTextPage
        parts = module_path.split(".")
        model_name = parts[-1]
        # app label is the package under mezzanine (pages, blog, …)
        if parts[0] == "mezzanine" and len(parts) >= 4:
            app_label = parts[1]
        else:
            app_label = parts[0]
    elif "." in dotted:
        app_label, model_name = dotted.split(".", 1)
    else:
        raise KitError("Invalid content_type %r" % dotted)

    try:
        model = django_apps.get_model(app_label, model_name)
    except LookupError as exc:
        raise KitError(
            "Unknown content_type %r (app=%s model=%s)"
            % (dotted, app_label, model_name)
        ) from exc
    return ContentType.objects.get_for_model(model)


def sync_field_schemas(name: str, *, fields_data: dict | None = None) -> list:
    """
    Upsert FieldSchema rows from a kit's fields.json (PR-059 / KD20).

    - Creates or updates schemas by (content_type, name).
    - Sets kit=name on every synced row.
    - Does not delete schemas absent from the file (safe re-activate).
    Returns the list of FieldSchema instances touched.
    """
    from mezzanine.core.models import FieldSchema

    if fields_data is None:
        fields_data = load_fields_json(name)
    if not fields_data:
        return []

    kit_name = str(fields_data.get("kit") or name).strip() or name
    results = []
    for entry in fields_data.get("fields") or []:
        ct = _resolve_content_type(entry["content_type"])
        defaults = {
            "kit": kit_name,
            "label": str(entry["label"]),
            "field_type": str(entry.get("field_type") or "text"),
            "required": bool(entry.get("required", False)),
            "order": int(entry.get("order") or 0),
            "options": entry.get("options")
            if isinstance(entry.get("options"), dict)
            else {},
        }
        obj, _created = FieldSchema.objects.update_or_create(
            content_type=ct,
            name=str(entry["name"]),
            defaults=defaults,
        )
        results.append(obj)
    return results


def apply_kit(name: str, project_dir: str | Path, project_app: str) -> dict:
    """
    Overlay a kit onto a project written by nova-project.

    - validates kit.json
    - copies shared + kit templates/static into the project
    - rewrites INSTALLED_APPS from kit types (blog optional)
    """
    root, meta = load_kit_meta(name)
    validate_kit(meta)
    project_dir = Path(project_dir)
    project_app_dir = project_dir / project_app

    # Settings first so a rewrite failure does not leave kit templates alone.
    # Blog from types; plugins from kit.json / music.* types (WP theme+plugins).
    _apply_kit_settings(
        project_app_dir,
        name,
        with_blog=kit_wants_blog(meta),
        plugins=kit_plugins(meta),
    )
    _apply_kit_urls(project_app_dir, meta)
    # KD20 / PR-059: validate fields.json shape at project create (DB sync needs
    # a configured Django app registry — operators run sync via activate-theme
    # or management command after migrate).
    load_fields_json(name)

    templates_dest = project_dir / "templates"
    if templates_dest.exists():
        shutil.rmtree(templates_dest)
    templates_dest.mkdir(parents=True, exist_ok=True)

    kits_root = Path(mezzanine.__path__[0]) / "kits"
    # Shared kit chrome first (kit_base.html), then kit-specific overlay.
    shared_templates = kits_root / "shared" / "templates"
    if shared_templates.is_dir():
        for item in shared_templates.iterdir():
            target = templates_dest / item.name
            if item.is_dir():
                shutil.copytree(item, target)
            else:
                shutil.copy2(item, target)

    templates_src = root / "templates"
    if templates_src.is_dir():
        for item in templates_src.iterdir():
            target = templates_dest / item.name
            if item.is_dir():
                # Merge so kit subdirs do not wipe shared includes/pages.
                target.mkdir(parents=True, exist_ok=True)
                for sub in item.rglob("*"):
                    rel = sub.relative_to(item)
                    dest = target / rel
                    if sub.is_dir():
                        dest.mkdir(parents=True, exist_ok=True)
                    else:
                        dest.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(sub, dest)
            else:
                shutil.copy2(item, target)

    # Shared static (layout utilities) then kit tokens/static overlay.
    static_dest = project_dir / "static"
    if static_dest.exists():
        shutil.rmtree(static_dest)
    static_dest.mkdir(parents=True, exist_ok=True)
    shared_static = kits_root / "shared" / "static"
    if shared_static.is_dir():
        for item in shared_static.iterdir():
            target = static_dest / item.name
            if item.is_dir():
                shutil.copytree(item, target)
            else:
                shutil.copy2(item, target)
    static_src = root / "static"
    if static_src.is_dir():
        for item in static_src.iterdir():
            target = static_dest / item.name
            if item.is_dir():
                if target.exists():
                    shutil.rmtree(target)
                shutil.copytree(item, target)
            else:
                shutil.copy2(item, target)

    (project_dir / ".nova-kit").write_text(name + "\n", encoding="utf-8")
    return meta


def _apply_kit_settings(
    project_app_dir: Path,
    kit_name: str,
    *,
    with_blog: bool,
    plugins: list[str] | None = None,
) -> None:
    """Rewrite INSTALLED_APPS for a first-party kit from its feature flags."""
    settings_path = project_app_dir / "settings.py"
    text = settings_path.read_text(encoding="utf-8")
    apps = [
        "django.contrib.admin",
        "django.contrib.auth",
        "django.contrib.contenttypes",
        "django.contrib.redirects",
        "django.contrib.sessions",
        "django.contrib.sites",
        "django.contrib.sitemaps",
        "django.contrib.messages",
        "django.contrib.staticfiles",
        f"mezzanine.kits.{kit_name}",
        "mezzanine.boot",
        "mezzanine.conf",
        "mezzanine.core",
        "mezzanine.generic",
        "mezzanine.pages",
        "mezzanine.forms",
        "mezzanine.migrate",
    ]
    if with_blog:
        apps.insert(apps.index("mezzanine.pages") + 1, "mezzanine.blog")
    for plugin in plugins or []:
        if not re.fullmatch(r"[\w.]+", plugin):
            raise KitError("Invalid kit plugin %r" % plugin)
        if plugin not in apps:
            # Plugins sit with other content apps (after pages).
            apps.insert(apps.index("mezzanine.forms") + 1, plugin)
    apps_block = "INSTALLED_APPS = [\n" + "".join(
        f'    "{app}",\n' for app in apps
    ) + "]"
    new_text, n = re.subn(
        r"INSTALLED_APPS\s*=\s*\[[^\]]*\]",
        apps_block,
        text,
        count=1,
        flags=re.S,
    )
    if n != 1:
        raise KitError("Could not rewrite INSTALLED_APPS for %s kit" % kit_name)
    if "STATICFILES_DIRS" not in new_text:
        new_text = new_text.replace(
            "STATIC_ROOT = os.path.join(PROJECT_ROOT, STATIC_URL.strip(\"/\"))",
            "STATIC_ROOT = os.path.join(PROJECT_ROOT, STATIC_URL.strip(\"/\"))\n"
            "STATICFILES_DIRS = [os.path.join(PROJECT_ROOT, \"static\")]",
            1,
        )
    # Editorial kits: comments off; featured images on for seed thumbs.
    if with_blog and "COMMENTS_DEFAULT_APPROVED" not in new_text:
        new_text += (
            f"\n# {kit_name.capitalize()} kit: comments off by default.\n"
            "COMMENTS_DEFAULT_APPROVED = False\n"
            "COMMENTS_ACCOUNT_REQUIRED = True\n"
        )
    if with_blog and "BLOG_USE_FEATURED_IMAGE" not in new_text:
        new_text += (
            "\n# Show featured images from seed / admin on list + detail.\n"
            "BLOG_USE_FEATURED_IMAGE = True\n"
        )
    settings_path.write_text(new_text, encoding="utf-8")


def _apply_brochure_settings(project_app_dir: Path) -> None:
    """Backward-compatible alias for tests."""
    _apply_kit_settings(project_app_dir, "brochure", with_blog=False, plugins=None)


def _apply_kit_urls(project_app_dir: Path, meta: dict) -> None:
    """
    Mount kit urlconf at site root when kit.json declares ``urlconf``.

    Replaces the default static ``index.html`` homepage pattern so player /
    app kits own ``/`` without fighting mezzanine.pages catch-all ordering.
    """
    urlconf = kit_urlconf(meta)
    if not urlconf:
        return
    if not re.fullmatch(r"[\w.]+", urlconf):
        raise KitError("Invalid kit urlconf %r" % urlconf)
    urls_path = project_app_dir / "urls.py"
    if not urls_path.is_file():
        raise KitError("Project urls.py missing; cannot mount kit urlconf")
    text = urls_path.read_text(encoding="utf-8")
    if urlconf in text and "include(\"%s\")" % urlconf in text:
        return
    # Strip any prior kit homepage include we may have written.
    text = re.sub(
        r'\n?\s*path\(""\s*,\s*include\("[^"]+"\)\),\s*'
        r"# kit urlconf \(nova\)\n",
        "\n",
        text,
    )
    home_static = (
        'path("", TemplateView.as_view(template_name="index.html"), name="home"),'
    )
    kit_home = (
        'path("", include("%s")),  # kit urlconf (nova)' % urlconf
    )
    if home_static in text:
        text = text.replace(home_static, kit_home, 1)
    else:
        # Insert before mezzanine.urls include.
        needle = 'path("", include("mezzanine.urls")),'
        if needle not in text:
            raise KitError("Could not mount kit urlconf in urls.py")
        text = text.replace(needle, kit_home + "\n    " + needle, 1)
    if "include" not in text.split("from django.urls import", 1)[-1].split("\n", 1)[0]:
        text = text.replace(
            "from django.urls import path",
            "from django.urls import include, path",
            1,
        )
    urls_path.write_text(text, encoding="utf-8")
