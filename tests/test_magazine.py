"""PR-033 Magazine kit — blog + pages for WP marketing/blog parity."""

from pathlib import Path

import mezzanine
from mezzanine.kits.loader import apply_kit, load_kit_meta, validate_kit

REPO = Path(mezzanine.__file__).resolve().parent.parent


def test_magazine_kit_json_shape():
    root, meta = load_kit_meta("magazine")
    assert meta["name"] == "magazine"
    assert "blog.BlogPost" in meta["types"]
    assert "pages.RichTextPage" in meta["types"]
    assert "signature" not in meta
    validate_kit(meta)
    assert (root / "static/magazine/tokens.css").is_file()
    assert (root / "fixtures/demo.json").is_file()
    assert (root / "templates/base.html").is_file()
    base = (root / "templates/base.html").read_text(encoding="utf-8")
    assert "kit_base.html" in base
    tokens = (root / "static/magazine/tokens.css").read_text(encoding="utf-8")
    assert "--nova-accent" in tokens
    assert "Source Serif" in tokens or "serif" in tokens


def test_apply_magazine_kit_rewrites_settings(tmp_path):
    project = tmp_path / "mag"
    app = "mysite"
    app_dir = project / app
    app_dir.mkdir(parents=True)
    (app_dir / "settings.py").write_text(
        "INSTALLED_APPS = [\n"
        '    "django.contrib.admin",\n'
        '    "mezzanine.core",\n'
        '    "mezzanine.pages",\n'
        "]\n"
        'STATIC_ROOT = os.path.join(PROJECT_ROOT, STATIC_URL.strip("/"))\n',
        encoding="utf-8",
    )
    apply_kit("magazine", project, app)
    text = (app_dir / "settings.py").read_text(encoding="utf-8")
    assert "mezzanine.kits.magazine" in text
    assert "mezzanine.blog" in text
    assert "mezzanine.forms" in text
    assert (project / ".nova-kit").read_text(encoding="utf-8").strip() == "magazine"
    assert (project / "static/magazine/tokens.css").is_file()
    assert "COMMENTS_DEFAULT_APPROVED = False" in text


def test_kit_help_lists_magazine():
    help_text = (
        REPO
        / "mezzanine/bin/management/commands/mezzanine_project.py"
    ).read_text(encoding="utf-8")
    assert "brochure" in help_text
