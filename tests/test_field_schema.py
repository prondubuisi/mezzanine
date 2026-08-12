"""PR-058 / KD20: FieldSchema model + Displayable.custom_fields (DESIGN Amendment 4).

Characterization: Displayable subclasses accept custom_fields JSON; FieldSchema
enforces unique (content_type, name) and type-aware clean_value.
"""

import pytest
from django.contrib.contenttypes.models import ContentType
from django.db import IntegrityError

from mezzanine.core.models import (
    FIELD_TYPE_BOOLEAN,
    FIELD_TYPE_CHOICE,
    FIELD_TYPE_NUMBER,
    FIELD_TYPE_TEXT,
    FieldSchema,
)
from mezzanine.pages.models import RichTextPage
from tests.factories import BlogPostFactory, RichTextPageFactory

pytestmark = pytest.mark.django_db


def test_displayable_custom_fields_default_empty_dict():
    """Characterization: new pages start with empty custom_fields."""
    page = RichTextPageFactory(title="No custom fields yet")
    assert not page.custom_fields  # {} or None
    # After save path, treat missing as empty for getters.
    assert page.get_custom_field("faculty_title") is None


def test_set_and_get_custom_field_roundtrip():
    page = RichTextPageFactory(title="Faculty profile")
    page.set_custom_field("faculty_title", "Associate Professor", save=True)
    page.refresh_from_db()
    assert page.get_custom_field("faculty_title") == "Associate Professor"
    assert page.custom_fields["faculty_title"] == "Associate Professor"


def test_blogpost_also_has_custom_fields():
    post = BlogPostFactory(title="Research story")
    post.set_custom_field("department", "Earth & Planetary", save=True)
    post.refresh_from_db()
    assert post.custom_fields["department"] == "Earth & Planetary"


def test_fieldschema_create_and_unique_constraint():
    ct = ContentType.objects.get_for_model(RichTextPage)
    FieldSchema.objects.create(
        kit="institute",
        content_type=ct,
        name="faculty_title",
        label="Faculty title",
        field_type=FIELD_TYPE_TEXT,
        required=True,
        order=0,
    )
    with pytest.raises(IntegrityError):
        FieldSchema.objects.create(
            kit="other",
            content_type=ct,
            name="faculty_title",
            label="Duplicate name",
            field_type=FIELD_TYPE_TEXT,
        )


def test_fieldschema_clean_value_types():
    ct = ContentType.objects.get_for_model(RichTextPage)
    text = FieldSchema(
        content_type=ct,
        name="office_hours",
        label="Office hours",
        field_type=FIELD_TYPE_TEXT,
        required=False,
    )
    assert text.clean_value("Tue 2pm") == "Tue 2pm"
    assert text.clean_value("") == ""

    required = FieldSchema(
        content_type=ct,
        name="faculty_title",
        label="Faculty title",
        field_type=FIELD_TYPE_TEXT,
        required=True,
    )
    with pytest.raises(ValueError, match="required"):
        required.clean_value("")

    number = FieldSchema(
        content_type=ct,
        name="years",
        label="Years",
        field_type=FIELD_TYPE_NUMBER,
    )
    assert number.clean_value("12") == 12
    assert number.clean_value(3.5) == 3.5
    with pytest.raises(ValueError, match="number"):
        number.clean_value("nope")

    boolean = FieldSchema(
        content_type=ct,
        name="tenured",
        label="Tenured",
        field_type=FIELD_TYPE_BOOLEAN,
    )
    assert boolean.clean_value(True) is True
    assert boolean.clean_value("yes") is True
    assert boolean.clean_value("false") is False

    choice = FieldSchema(
        content_type=ct,
        name="department",
        label="Department",
        field_type=FIELD_TYPE_CHOICE,
        options={"choices": ["Earth & Planetary", "Public Policy"]},
    )
    assert choice.clean_value("Public Policy") == "Public Policy"
    with pytest.raises(ValueError, match="one of"):
        choice.clean_value("Agriculture")


def test_fieldschema_str():
    ct = ContentType.objects.get_for_model(RichTextPage)
    schema = FieldSchema.objects.create(
        content_type=ct,
        name="faculty_title",
        label="Faculty title",
        field_type=FIELD_TYPE_TEXT,
    )
    assert "faculty_title" in str(schema)
