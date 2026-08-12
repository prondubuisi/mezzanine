"""PR-029 page tree assets; PR-030 extras; Postgres FTS hook."""

from pathlib import Path

import pytest
from django.test import override_settings

import mezzanine
from mezzanine.core.models import CONTENT_STATUS_PUBLISHED
from mezzanine.pages.models import RichTextPage

REPO = Path(mezzanine.__file__).resolve().parent


def test_nested_sortable_removed():
    admin_js = REPO / "pages/static/mezzanine/js/admin"
    assert not (admin_js / "jquery.mjs.nestedSortable.js").exists()
    page_tree = (admin_js / "page_tree.js").read_text(encoding="utf-8")
    assert "nestedSortable(" not in page_tree
    assert ".sortable(" in page_tree
    assert "connectWith" in page_tree
    cl = (
        REPO / "pages/templates/admin/pages/page/change_list.html"
    ).read_text(encoding="utf-8")
    assert "jquery.mjs.nestedSortable" not in cl
    assert "page_tree.js" in cl


def test_grappelli_filebrowser_are_optional_extras():
    text = (REPO.parent / "pyproject.toml").read_text(encoding="utf-8")
    # Kernel deps must not hard-require the skins.
    deps_block = text.split("[project.optional-dependencies]", 1)[0]
    assert "grappelli_safe" not in deps_block
    assert "filebrowser_safe" not in deps_block
    assert "grappelli = [" in text
    assert "filebrowser = [" in text
    settings_py = (
        REPO / "project_template/project_name/settings.py"
    ).read_text(encoding="utf-8")
    # Default OPTIONAL_APPS no longer lists them (PR-030).
    opt = settings_py.split("OPTIONAL_APPS", 1)[1].split(")", 1)[0]
    assert "PACKAGE_NAME_FILEBROWSER" not in opt
    assert "PACKAGE_NAME_GRAPPELLI" not in opt


@pytest.mark.django_db
def test_search_icontains_still_works_on_sqlite():
    """Default test DB is sqlite — FTS falls back; drafts stay out."""
    RichTextPage.objects.all().delete()
    RichTextPage.objects.create(title="alpha draft", status=1)
    published = RichTextPage.objects.create(
        title="alpha published page",
        status=CONTENT_STATUS_PUBLISHED,
        content="<p>alpha body</p>",
    )
    results = list(RichTextPage.objects.search("alpha"))
    ids = [r.id for r in results]
    assert published.id in ids
    assert all(r.status == CONTENT_STATUS_PUBLISHED for r in results)


@pytest.mark.django_db
@override_settings(SEARCH_USE_POSTGRES_FTS=False)
def test_search_can_disable_fts_flag():
    RichTextPage.objects.all().delete()
    RichTextPage.objects.create(
        title="beta published",
        status=CONTENT_STATUS_PUBLISHED,
    )
    results = list(RichTextPage.objects.search("beta"))
    assert len(results) == 1
