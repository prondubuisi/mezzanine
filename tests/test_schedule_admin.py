"""Displayable admin schedule UI (publish_date / expiry_date)."""

from mezzanine.core.admin import DisplayableAdmin


def test_displayable_admin_has_schedule_fieldset():
    titles = [fs[0] for fs in DisplayableAdmin.fieldsets]
    assert any(t and "schedule" in str(t).lower() for t in titles)
    # publish + expiry still present
    flat = []
    for _title, opts in DisplayableAdmin.fieldsets:
        for item in opts.get("fields", []):
            if isinstance(item, (list, tuple)):
                flat.extend(item)
            else:
                flat.append(item)
    assert "publish_date" in flat
    assert "expiry_date" in flat
    assert "status" in flat


def test_displayable_admin_list_shows_schedule_columns():
    assert "publish_date" in DisplayableAdmin.list_display
    assert "expiry_date" in DisplayableAdmin.list_display
    assert "publish_date" in DisplayableAdmin.list_filter
    assert "expiry_date" in DisplayableAdmin.list_filter
