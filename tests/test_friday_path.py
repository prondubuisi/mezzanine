"""End-to-end Friday path smoke (A0′ success metric)."""

import os
import subprocess
import sys
from pathlib import Path

import mezzanine

REPO_ROOT = Path(mezzanine.__file__).resolve().parent.parent
PROJECT = "novademo"


def _run_nova_project(tmp_path, *extra):
    env = os.environ.copy()
    env.pop("DJANGO_SETTINGS_MODULE", None)
    env["PYTHONPATH"] = str(REPO_ROOT) + os.pathsep + env.get("PYTHONPATH", "")
    argv = ["nova-project", PROJECT, *extra]
    return subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys; sys.argv = %r; "
                "from mezzanine.bin.mezzanine_project import create_project; "
                "create_project()"
            )
            % list(argv),
        ],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def test_friday_path_brochure_createdb_and_import(tmp_path):
    """
    uvx nova-project … --kit brochure → migrate → createdb demo → import WXR pages.

    Uses sqlite so the smoke does not need Docker/Postgres.
    """
    result = _run_nova_project(tmp_path, "--kit", "brochure")
    assert result.returncode == 0, result.stderr or result.stdout
    project = tmp_path / PROJECT
    assert (project / ".nova-kit").read_text().strip() == "brochure"

    # Force sqlite for the smoke (template prefers postgres when env is set).
    local = project / PROJECT / "local_settings.py"
    local.write_text(
        local.read_text(encoding="utf-8")
        + "\n\nDATABASES = {\n"
        "    'default': {\n"
        "        'ENGINE': 'django.db.backends.sqlite3',\n"
        "        'NAME': %r,\n"
        "    }\n"
        "}\n" % str(project / "smoke.db"),
        encoding="utf-8",
    )

    env = os.environ.copy()
    env.pop("DJANGO_SETTINGS_MODULE", None)
    env["PYTHONPATH"] = (
        str(project)
        + os.pathsep
        + str(REPO_ROOT)
        + os.pathsep
        + env.get("PYTHONPATH", "")
    )
    manage = [sys.executable, str(project / "manage.py")]

    def mgmt(*args):
        return subprocess.run(
            [*manage, *args],
            cwd=project,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )

    # createdb runs migrate itself; just bootstrap is createdb || migrate.
    createdb = mgmt("createdb", "--noinput")
    assert createdb.returncode == 0, createdb.stderr or createdb.stdout

    probe = mgmt(
        "shell",
        "-c",
        "from mezzanine.pages.models import Page; "
        "from mezzanine.forms.models import Form; "
        "print(sorted(Page.objects.values_list('title', flat=True))); "
        "print(Form.objects.count())",
    )
    assert probe.returncode == 0, probe.stderr or probe.stdout
    assert "About" in probe.stdout
    assert "Contact" in probe.stdout
    assert "Services" in probe.stdout

    wxr = REPO_ROOT / "tests" / "fixtures" / "wxr_sample.xml"
    imported = mgmt(
        "import_wordpress",
        "--mezzanine-user=admin",
        "--url=%s" % wxr,
        "--noinput",
        "--verbosity=0",
    )
    assert imported.returncode == 0, imported.stderr or imported.stdout

    pages = mgmt(
        "shell",
        "-c",
        "from mezzanine.pages.models import Page; "
        "from django.contrib.redirects.models import Redirect; "
        "print('Team' in set(Page.objects.values_list('title', flat=True))); "
        "print(Redirect.objects.filter(old_path='/about/').exists())",
    )
    assert pages.returncode == 0, pages.stderr or pages.stdout
    assert "True" in pages.stdout
