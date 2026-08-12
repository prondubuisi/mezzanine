"""Brochure kit + Friday path (PR-031 / PR-032)."""

import json
import os
import re
import subprocess
import sys
from pathlib import Path

import mezzanine
from mezzanine.kits.loader import KitError, load_kit_meta, validate_kit

REPO_ROOT = Path(mezzanine.__file__).resolve().parent.parent


def test_brochure_kit_json_shape():
    root, meta = load_kit_meta("brochure")
    assert meta["name"] == "brochure"
    assert meta["version"] == "0.1.0"
    assert meta["nova_compat"] == ">=0.1,<2"
    assert "signature" not in meta
    assert set(meta["types"]) == {
        "pages.RichTextPage",
        "pages.Link",
        "forms.Form",
    }
    assert meta["tokens"] == "static/brochure/tokens.css"
    assert (root / "static" / "brochure" / "tokens.css").is_file()
    assert (root / "fixtures" / "demo.json").is_file()
    assert (root / "templates" / "base.html").is_file()


def test_brochure_kit_validates():
    _, meta = load_kit_meta("brochure")
    validate_kit(meta)  # uses 9999dev0 special-case


def test_kit_rejects_incompatible_version():
    _, meta = load_kit_meta("brochure")
    try:
        validate_kit(meta, version="3.0.0")
        raise AssertionError("expected KitError")
    except KitError as exc:
        assert "nova_compat" in str(exc)


def test_kit_rejects_unknown_name():
    try:
        load_kit_meta("not-a-real-kit")
        raise AssertionError("expected KitError")
    except KitError as exc:
        assert "Unknown kit" in str(exc)


def test_bs3_compat_css_exists():
    path = REPO_ROOT / "mezzanine/core/static/css/bs3-compat.css"
    assert path.is_file()
    text = path.read_text()
    assert ".container" in text
    assert ".col-md-7" in text


def test_core_base_html_staff_only_jquery():
    text = (REPO_ROOT / "mezzanine/core/templates/base.html").read_text()
    assert "user.is_staff" in text
    assert "JQUERY_FILENAME" in text
    # jQuery script tag must sit inside the staff guard, not load for public.
    guard = text.split("user.is_staff", 1)[1]
    assert "JQUERY_FILENAME" in guard.split("{% endif %}", 1)[0]


def test_brochure_demo_fixture_types():
    data = json.loads(
        (REPO_ROOT / "mezzanine/kits/brochure/fixtures/demo.json").read_text()
    )
    models = {row["model"] for row in data}
    assert "pages.page" in models
    assert "pages.richtextpage" in models
    assert "forms.form" in models
    assert "forms.field" in models
    assert "blog.blogpost" not in models
    assert "galleries.gallery" not in models
    content_models = {
        row["fields"]["content_model"]
        for row in data
        if row["model"] == "pages.page"
    }
    assert content_models <= {"richtextpage", "form", "link"}


def _run_nova_project(tmp_path, *extra_argv):
    env = os.environ.copy()
    env.pop("DJANGO_SETTINGS_MODULE", None)
    env["PYTHONPATH"] = str(REPO_ROOT) + os.pathsep + env.get("PYTHONPATH", "")
    argv = ["nova-project", "mysite", *extra_argv]
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys; "
                "sys.argv = %r; "
                "from mezzanine.bin.mezzanine_project import create_project; "
                "create_project()"
            )
            % argv,
        ],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    return result


def test_nova_project_kit_brochure(tmp_path):
    result = _run_nova_project(tmp_path, "--kit", "brochure")
    assert result.returncode == 0, result.stderr or result.stdout
    project = tmp_path / "mysite"
    settings_text = (project / "mysite" / "settings.py").read_text()
    assert '"mezzanine.kits.brochure"' in settings_text
    assert '"mezzanine.forms"' in settings_text
    assert '"mezzanine.blog"' not in settings_text
    assert '"mezzanine.galleries"' not in settings_text
    assert (project / ".nova-kit").read_text().strip() == "brochure"
    assert (project / "static" / "brochure" / "tokens.css").is_file()
    assert (project / "templates" / "base.html").is_file()
    base = (project / "templates" / "base.html").read_text()
    assert "brochure/tokens.css" in base
    assert "bs3-compat.css" in base
    assert "user.is_staff" in base


def test_nova_project_unknown_kit_fails(tmp_path):
    result = _run_nova_project(tmp_path, "--kit", "institute")
    assert result.returncode != 0
    combined = (result.stderr or "") + (result.stdout or "")
    assert "Unknown kit" in combined or "institute" in combined


def test_overview_documents_kit_brochure():
    text = (REPO_ROOT / "docs/overview.rst").read_text()
    assert "--kit brochure" in text
    assert re.search(r"just bootstrap", text)
