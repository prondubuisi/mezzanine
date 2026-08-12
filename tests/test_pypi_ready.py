"""PyPI pre-release readiness checks (no network upload)."""

import re
from pathlib import Path

import mezzanine

REPO = Path(mezzanine.__file__).resolve().parent.parent


def test_version_is_dev_sentinel():
    # hatchling + semantic-release mutate this at release time.
    assert re.match(r"^\d", mezzanine.__version__)
    assert "dev" in mezzanine.__version__ or mezzanine.__version__ == "9999dev0"


def test_pyproject_names_nova_cms():
    text = (REPO / "pyproject.toml").read_text(encoding="utf-8")
    assert 'name = "nova-cms"' in text
    assert "[tool.hatch.version]" in text
    assert 'path = "mezzanine/__init__.py"' in text


def test_publish_workflow_uses_trusted_publishing():
    yml = (REPO / ".github/workflows/publish.yml").read_text(encoding="utf-8")
    assert "id-token: write" in yml
    assert "pypa/gh-action-pypi-publish" in yml
    assert "environment:" in yml
    assert "pypi" in yml
    assert "skip-existing: true" in yml
    # Must not wire a long-lived token secret (comment may mention PYPI_TOKEN).
    assert "secrets.PYPI_TOKEN" not in yml
    assert "password:" not in yml


def test_readme_documents_pypi_trusted_publishing():
    readme = (REPO / "README.rst").read_text(encoding="utf-8")
    assert "Trusted Publishing" in readme
    assert "publish.yml" in readme
    assert "nova-cms" in readme
