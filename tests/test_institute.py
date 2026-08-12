"""Y2 Institute kit scaffold — higher-ed marketing starter."""

from pathlib import Path

import mezzanine
from mezzanine.kits.loader import apply_kit, load_kit_meta, validate_kit

REPO = Path(mezzanine.__file__).resolve().parent.parent


def test_institute_kit_json_shape():
    root, meta = load_kit_meta("institute")
    assert meta["name"] == "institute"
    assert "blog.BlogPost" in meta["types"]
    assert "forms.Form" in meta["types"]
    assert "pages.RichTextPage" in meta["types"]
    assert "signature" not in meta
    validate_kit(meta)
    assert (root / "static/institute/tokens.css").is_file()
    assert (root / "fixtures/demo.json").is_file()
    assert (root / "templates/base.html").is_file()
    tokens = (root / "static/institute/tokens.css").read_text(encoding="utf-8")
    assert "--nova-accent" in tokens
    assert "1d4ed8" in tokens or "Institute" in tokens


def test_apply_institute_kit_rewrites_settings(tmp_path):
    project = tmp_path / "inst"
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
    apply_kit("institute", project, app)
    text = (app_dir / "settings.py").read_text(encoding="utf-8")
    assert "mezzanine.kits.institute" in text
    assert "mezzanine.blog" in text
    assert "mezzanine.forms" in text
    assert (project / ".nova-kit").read_text(encoding="utf-8").strip() == "institute"
    assert (project / "static/institute/tokens.css").is_file()


def test_kit_help_lists_institute():
    help_text = (
        REPO
        / "mezzanine/bin/management/commands/mezzanine_project.py"
    ).read_text(encoding="utf-8")
    assert "institute" in help_text
