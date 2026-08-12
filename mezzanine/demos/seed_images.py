"""
Generate lightweight placeholder featured images for IA demo seeds.

Uses Pillow (already a project dependency). Deterministic colors per slug
so re-seeds stay stable without shipping binary fixtures.
"""

from __future__ import annotations

import hashlib
from io import BytesIO


def placeholder_png(slug: str, *, size: int = 480) -> bytes:
    """Return PNG bytes for a solid/gradient-ish cover labeled with slug."""
    from PIL import Image, ImageDraw, ImageFont

    digest = hashlib.sha256(slug.encode("utf-8")).digest()
    # Pleasant mid-tone palette from hash
    r, g, b = 40 + digest[0] % 160, 40 + digest[1] % 160, 40 + digest[2] % 160
    r2, g2, b2 = (r + 40) % 220, (g + 60) % 220, (b + 80) % 220
    img = Image.new("RGB", (size, size), (r, g, b))
    draw = ImageDraw.Draw(img)
    # Soft diagonal band
    draw.polygon(
        [(0, size // 3), (size, 0), (size, size // 2), (0, size)],
        fill=(r2, g2, b2),
    )
    label = (slug.replace("-", " ")[:28] or "story").title()
    try:
        font = ImageFont.load_default()
    except Exception:  # noqa: BLE001
        font = None
    # Shadow + text
    tx, ty = 24, size - 48
    draw.text((tx + 1, ty + 1), label, fill=(0, 0, 0), font=font)
    draw.text((tx, ty), label, fill=(255, 255, 255), font=font)
    buf = BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return buf.getvalue()
