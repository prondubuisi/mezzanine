"""CSP nonce attributes on Mezzanine-owned templates."""

from pathlib import Path

import mezzanine

REPO = Path(mezzanine.__file__).resolve().parent


def test_csp_nonce_tag_defined():
    from mezzanine.core.templatetags import mezzanine_tags as tags

    assert hasattr(tags, "csp_nonce")


def test_admin_base_site_scripts_use_csp_nonce():
    text = (REPO / "core/templates/admin/base_site.html").read_text(encoding="utf-8")
    assert "{% csp_nonce %}" in text
    assert text.count("csp_nonce") >= 4


def test_editable_loader_and_base_use_nonce():
    editable = (REPO / "core/templates/includes/editable_loader.html").read_text(
        encoding="utf-8"
    )
    assert "csp_nonce" in editable
    base = (REPO / "core/templates/base.html").read_text(encoding="utf-8")
    assert "csp_nonce" in base
