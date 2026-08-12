"""PR-042 / R2: extend_fieldsets helper (DESIGN.md Amendment 2)."""

from mezzanine.core.admin import DisplayableAdmin, extend_fieldsets


def test_extend_fieldsets_appends_and_does_not_mutate_base():
    base = DisplayableAdmin.fieldsets
    base_first = list(base[0][1]["fields"])
    result = extend_fieldsets(base, ["login_required", "in_menus"])
    assert result[0][1]["fields"][-2:] == ["login_required", "in_menus"]
    # Base unchanged
    assert list(base[0][1]["fields"]) == base_first
    assert "login_required" not in base[0][1]["fields"]


def test_extend_fieldsets_insert_fields_and_group():
    base = (
        (None, {"fields": ["title", "status", "slug"]}),
        ("Meta", {"fields": ["keywords"]}),
    )
    result = extend_fieldsets(
        base,
        [
            (1, "categories"),
            (3, ["content", "button_text"]),
            "allow_comments",
            (
                1,
                ("Other", {"classes": ("collapse-closed",), "fields": ("related",)}),
            ),
        ],
    )
    assert result[0][1]["fields"] == [
        "title",
        "categories",
        "status",
        "content",
        "button_text",
        "slug",
        "allow_comments",
    ]
    assert result[1][0] == "Other"
    assert result[1][1]["fields"] == ("related",)
    assert result[2][0] == "Meta"


def test_extend_fieldsets_negative_insert():
    base = ((None, {"fields": ["a", "b", "c", "d"]}),)
    result = extend_fieldsets(base, [(-2, "x")])
    assert result[0][1]["fields"] == ["a", "b", "x", "c", "d"]
