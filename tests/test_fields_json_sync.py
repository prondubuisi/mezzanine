"""PR-059 / KD20: kit fields.json loading + FieldSchema activation sync.

DESIGN.md Amendment 4 §A4.2 — fields.json reuses kit_path containment;
sync runs on set_active_theme when present.
"""

import json
from pathlib import Path

import pytest
from django.contrib.contenttypes.models import ContentType

from mezzanine.core.models import FieldSchema
from mezzanine.kits.loader import (
    KitError,
    fields_json_path,
    load_fields_json,
    sync_field_schemas,
)
from mezzanine.pages.models import RichTextPage

pytestmark = pytest.mark.django_db


def test_institute_fields_json_loads():
    data = load_fields_json("institute")
    assert data is not None
    assert data["kit"] == "institute"
    names = [f["name"] for f in data["fields"]]
    assert names == ["faculty_title", "department", "office_hours"]
    assert fields_json_path("institute").is_file()


def test_brochure_has_no_fields_json():
    assert load_fields_json("brochure") is None


def test_sync_field_schemas_creates_rows():
    created = sync_field_schemas("institute")
    assert len(created) == 3
    ct = ContentType.objects.get_for_model(RichTextPage)
    title = FieldSchema.objects.get(content_type=ct, name="faculty_title")
    assert title.label == "Faculty title"
    assert title.required is True
    assert title.kit == "institute"
    dept = FieldSchema.objects.get(content_type=ct, name="department")
    assert dept.field_type == "choice"
    assert "Earth & Planetary" in (dept.options or {}).get("choices", [])


def test_sync_field_schemas_is_idempotent():
    sync_field_schemas("institute")
    sync_field_schemas("institute")
    ct = ContentType.objects.get_for_model(RichTextPage)
    assert FieldSchema.objects.filter(content_type=ct).count() == 3


def test_sync_updates_label_on_change(tmp_path, monkeypatch):
    # Use real institute data then re-sync with an in-memory override.
    data = load_fields_json("institute")
    assert data is not None
    data = json.loads(json.dumps(data))
    data["fields"][0]["label"] = "Title (updated)"
    sync_field_schemas("institute", fields_data=data)
    ct = ContentType.objects.get_for_model(RichTextPage)
    assert (
        FieldSchema.objects.get(content_type=ct, name="faculty_title").label
        == "Title (updated)"
    )


def test_load_fields_json_rejects_bad_name(tmp_path, monkeypatch):
    # Point kit_path at a temp kit with invalid fields.json via monkeypatch.
    import mezzanine.kits.loader as loader

    kit_dir = tmp_path / "kits" / "badkit"
    kit_dir.mkdir(parents=True)
    (kit_dir / "fields.json").write_text(
        json.dumps(
            {
                "fields": [
                    {
                        "content_type": "pages.RichTextPage",
                        "name": "Bad-Name",
                        "label": "X",
                        "field_type": "text",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    def fake_kit_path(name: str) -> Path:
        if name != "badkit":
            raise KitError("unknown")
        return kit_dir

    monkeypatch.setattr(loader, "kit_path", fake_kit_path)
    with pytest.raises(KitError, match="invalid name"):
        load_fields_json("badkit")


def test_set_active_theme_syncs_institute_fields():
    # Institute may not declare theme slots; set_active_theme requires theme meta.
    # Call sync path directly if institute is not a "theme"; if it is, activate.
    from mezzanine.kits.theme import ThemeError, load_theme_meta, set_active_theme

    try:
        load_theme_meta("institute")
    except ThemeError:
        pytest.skip("institute is not a loadable theme package")
    set_active_theme("institute")
    ct = ContentType.objects.get_for_model(RichTextPage)
    assert FieldSchema.objects.filter(content_type=ct, kit="institute").count() == 3
