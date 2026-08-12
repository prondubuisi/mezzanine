"""PR-045 / S1: theme customizer color validation (stored XSS)."""

import pytest

from mezzanine.kits.theme import (
    normalize_theme_color,
    set_active_theme,
    set_theme_customizer,
    theme_customizer_css,
)

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("#abc", "#abc"),
        ("#AABBCC", "#aabbcc"),
        ("#ff00ff00", "#ff00ff00"),
        ("  #123456  ", "#123456"),
        ("transparent", "transparent"),
        ("", ""),
        ("red", "red"),
    ],
)
def test_normalize_theme_color_accepts_safe_values(raw, expected):
    assert normalize_theme_color(raw) == expected


@pytest.mark.parametrize(
    "raw",
    [
        "red;}</style><script>alert(1)</script>",
        "expression(alert(1))",
        "url(javascript:alert(1))",
        "#gg0000",
        "not-a-color",
        "#12",
        "#12345",
        "rgb(0,0,0)",
        "var(--x)",
        "x" * 65,
    ],
)
def test_normalize_theme_color_rejects_unsafe_values(raw):
    assert normalize_theme_color(raw) is None


def test_set_theme_customizer_drops_xss_payload():
    set_active_theme("whitehouse")
    set_theme_customizer(colors={"accent": "#00ff00"})
    set_theme_customizer(
        colors={
            "accent": "red;}</style><script>alert(1)</script>",
            "ink": "#111111",
        }
    )
    css = theme_customizer_css()
    assert "<script" not in css
    assert "alert" not in css
    # Prior valid accent retained; new valid ink applied.
    assert "--nova-accent: #00ff00" in css
    assert "--nova-ink: #111111" in css


def test_theme_customizer_css_never_emits_raw_injection():
    set_active_theme("whitehouse")
    # Simulate a pre-existing bad Setting row (bypassing set_theme_customizer).
    from mezzanine.conf.models import Setting

    Setting.objects.update_or_create(
        name="THEME_COLOR_ACCENT",
        defaults={"value": "red;}</style><script>alert(1)</script>"},
    )
    from mezzanine.conf import settings as msettings

    if hasattr(msettings, "clear_cache"):
        msettings.clear_cache()
    css = theme_customizer_css()
    assert "<script" not in css
    assert "</style>" not in css or css.count("</style>") == 0
    # Malicious value must not appear as a CSS property value.
    assert "alert" not in css
