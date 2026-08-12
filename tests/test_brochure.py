"""Brochure kit + Friday path (PR-031 / PR-032)."""

import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.contrib.messages.storage.fallback import FallbackStorage
from django.core.management import call_command
from django.template.loader import get_template
from django.test import RequestFactory, override_settings

import mezzanine
from mezzanine.core.management.commands.createdb import Command as CreateDBCommand
from mezzanine.forms.models import Form
from mezzanine.kits.loader import (
    KitError,
    _compat_ok,
    apply_kit,
    load_kit_meta,
    validate_kit,
)
from mezzanine.pages.models import Page, RichTextPage

REPO_ROOT = Path(mezzanine.__file__).resolve().parent.parent
User = get_user_model()

# Brochure apps only — matches --kit brochure rewrite.
BROCHURE_APPS = [
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
    "filebrowser_safe",
    "grappelli_safe",
    "tests",
]


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


@pytest.mark.parametrize(
    "version,spec,ok",
    [
        ("9999dev0", ">=0.1,<2", True),
        ("0.1.0", ">=0.1,<2", True),
        ("1.9.0", ">=0.1,<2", True),
        ("0.0.9", ">=0.1,<2", False),
        ("2.0.0", ">=0.1,<2", False),
        ("3.0.0", ">=0.1,<2", False),
        ("1.0.0", ">=1,<1.5", True),
        ("1.5.0", ">=1,<1.5", False),
    ],
)
def test_compat_ok_matrix(version, spec, ok):
    assert _compat_ok(spec, version) is ok


def test_kit_rejects_incompatible_version():
    _, meta = load_kit_meta("brochure")
    with pytest.raises(KitError, match="nova_compat"):
        validate_kit(meta, version="3.0.0")


def test_kit_rejects_unknown_name():
    with pytest.raises(KitError, match="Unknown kit"):
        load_kit_meta("not-a-real-kit")


def test_kit_rejects_path_traversal_name():
    with pytest.raises(KitError, match="Invalid kit name"):
        load_kit_meta("../core")


def test_kit_rejects_signed_meta():
    with pytest.raises(KitError, match="unsigned"):
        validate_kit(
            {
                "name": "evil",
                "nova_compat": ">=0.1,<2",
                "types": [],
                "signature": "deadbeef",
            },
            version="0.1.0",
        )


def test_kit_rejects_missing_type_class(tmp_path, monkeypatch):
    """Type module exists but class name does not."""
    root = tmp_path / "kits" / "ghost"
    root.mkdir(parents=True)
    (root / "kit.json").write_text(
        json.dumps(
            {
                "name": "ghost",
                "nova_compat": ">=0.1,<2",
                "types": ["pages.NotARealModel"],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        "mezzanine.kits.loader.kit_path", lambda name: tmp_path / "kits" / name
    )
    _, meta = load_kit_meta("ghost")
    with pytest.raises(KitError, match="NotARealModel"):
        validate_kit(meta, version="0.1.0")


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


def _render_base(user):
    request = RequestFactory().get("/")
    request.user = user
    request.session = {}
    request._messages = FallbackStorage(request)
    return get_template("base.html").render({}, request=request)


@pytest.mark.django_db
def test_base_html_jquery_absent_for_anonymous():
    html = _render_base(AnonymousUser())
    assert "jquery" not in html.lower()
    assert "bootstrap.js" not in html


@pytest.mark.django_db
def test_base_html_jquery_present_for_staff():
    staff = User.objects.create_user(
        "staffer", "s@example.com", "passwordpassword", is_staff=True
    )
    html = _render_base(staff)
    assert "jquery" in html.lower()
    assert "bootstrap.js" in html


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
    # MTI pks for Form/RichTextPage must match their Page row.
    page_pks = {
        row["pk"]: row["fields"]["content_model"]
        for row in data
        if row["model"] == "pages.page"
    }
    for row in data:
        if row["model"] == "pages.richtextpage":
            assert page_pks[row["pk"]] == "richtextpage"
        if row["model"] == "forms.form":
            assert page_pks[row["pk"]] == "form"


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
    assert '"mezzanine.accounts"' not in settings_text
    assert "STATICFILES_DIRS" in settings_text
    assert (project / ".nova-kit").read_text().strip() == "brochure"
    assert (project / "static" / "brochure" / "tokens.css").is_file()
    assert (project / "templates" / "base.html").is_file()
    base = (project / "templates" / "base.html").read_text()
    assert "brochure/tokens.css" in base
    assert "bs3-compat.css" in base
    assert "user.is_staff" in base
    # No public jQuery on brochure base either.
    guard = base.split("user.is_staff", 1)[1]
    assert "JQUERY_FILENAME" in guard.split("{% endif %}", 1)[0]


def test_nova_project_without_kit_keeps_blog(tmp_path):
    result = _run_nova_project(tmp_path)
    assert result.returncode == 0, result.stderr or result.stdout
    settings_text = (tmp_path / "mysite" / "mysite" / "settings.py").read_text()
    assert '"mezzanine.blog"' in settings_text
    assert '"mezzanine.kits.brochure"' not in settings_text
    assert not (tmp_path / "mysite" / ".nova-kit").exists()


def test_nova_project_unknown_kit_fails(tmp_path):
    result = _run_nova_project(tmp_path, "--kit", "institute")
    assert result.returncode != 0
    combined = (result.stderr or "") + (result.stdout or "")
    assert "Unknown kit" in combined or "institute" in combined


def test_apply_kit_overwrites_templates(tmp_path):
    project = tmp_path / "mysite"
    app = project / "mysite"
    app.mkdir(parents=True)
    (app / "settings.py").write_text(
        (REPO_ROOT / "mezzanine/project_template/project_name/settings.py").read_text(),
        encoding="utf-8",
    )
    (project / "templates").mkdir()
    (project / "templates" / "base.html").write_text("OLD", encoding="utf-8")
    apply_kit("brochure", project, "mysite")
    assert "brochure/tokens.css" in (
        project / "templates" / "base.html"
    ).read_text(encoding="utf-8")
    assert (project / "static" / "brochure" / "tokens.css").is_file()


@pytest.mark.django_db
@override_settings(INSTALLED_APPS=BROCHURE_APPS)
def test_createdb_loads_brochure_demo():
    Page.objects.all().delete()
    cmd = CreateDBCommand()
    cmd.verbosity = 0
    cmd.interactive = False
    cmd.no_data = False
    cmd.create_pages()
    titles = set(Page.objects.values_list("title", flat=True))
    assert {"About", "Services", "Contact", "Team"} <= titles
    assert Form.objects.count() == 1
    assert RichTextPage.objects.count() >= 3
    # No blog page from mezzanine_required.
    assert not Page.objects.filter(slug="blog").exists()


@pytest.mark.django_db
@override_settings(INSTALLED_APPS=BROCHURE_APPS)
def test_createdb_brochure_respects_nodata():
    Page.objects.all().delete()
    cmd = CreateDBCommand()
    cmd.verbosity = 0
    cmd.interactive = False
    cmd.no_data = True
    cmd.create_pages()
    assert Page.objects.count() == 0


def test_overview_documents_kit_brochure():
    text = (REPO_ROOT / "docs/overview.rst").read_text()
    assert "--kit brochure" in text
    assert re.search(r"just bootstrap", text)
    assert "does not take a kit argument" in text


def test_form_template_has_no_jquery_api():
    text = (REPO_ROOT / "mezzanine/forms/templates/pages/form.html").read_text()
    # Script body must not call the jQuery API (comment text is fine).
    script = text.split("<script>", 1)[1].split("</script>", 1)[0]
    assert "$(" not in script
    assert "jQuery" not in script
    assert "querySelector" in script


def test_unknown_kit_fails_before_project_dir(tmp_path):
    result = _run_nova_project(tmp_path, "--kit", "not-a-kit")
    assert result.returncode != 0
    assert not (tmp_path / "mysite").exists()
