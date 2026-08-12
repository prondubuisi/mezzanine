"""Nova document body schema (PR-025 / KD7).

Y1.5 v1 schema is html-only blocks::

    {"$schema": "nova.document.v1", "blocks": [{"type": "html", "html": "<p>…</p>"}]}

``content`` remains the HTML projection for templates and search.
"""

from __future__ import annotations

import json
from typing import Any

SCHEMA_ID = "nova.document.v1"
BLOCK_TYPE_HTML = "html"


def empty_body() -> dict[str, Any]:
    return {"$schema": SCHEMA_ID, "blocks": []}


def body_from_html(html: str) -> dict[str, Any]:
    """Wrap an HTML string into a v1 document body (N migration path)."""
    text = html or ""
    if not text.strip():
        return empty_body()
    return {
        "$schema": SCHEMA_ID,
        "blocks": [{"type": BLOCK_TYPE_HTML, "html": text}],
    }


def html_from_body(body: Any) -> str:
    """Flatten a document body to HTML for ``content`` / templates."""
    if not body:
        return ""
    if isinstance(body, str):
        try:
            body = json.loads(body)
        except (TypeError, ValueError, json.JSONDecodeError):
            return body
    if not isinstance(body, dict):
        return ""
    parts: list[str] = []
    for block in body.get("blocks") or []:
        if not isinstance(block, dict):
            continue
        if block.get("type") == BLOCK_TYPE_HTML:
            parts.append(str(block.get("html") or ""))
    return "".join(parts)


def normalize_body(value: Any) -> dict[str, Any]:
    """Coerce DB/admin input into a validated v1 body dict."""
    if value in (None, "", {}):
        return empty_body()
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except (TypeError, ValueError, json.JSONDecodeError) as exc:
            raise ValueError("body must be valid JSON") from exc
    if not isinstance(value, dict):
        raise ValueError("body must be a JSON object")
    blocks = value.get("blocks")
    if blocks is None:
        blocks = []
    if not isinstance(blocks, list):
        raise ValueError("body.blocks must be a list")
    clean_blocks = []
    for block in blocks:
        if not isinstance(block, dict):
            raise ValueError("each block must be an object")
        btype = block.get("type")
        if btype != BLOCK_TYPE_HTML:
            raise ValueError(
                "v1 schema only allows type=%r blocks (got %r)"
                % (BLOCK_TYPE_HTML, btype)
            )
        clean_blocks.append(
            {"type": BLOCK_TYPE_HTML, "html": str(block.get("html") or "")}
        )
    return {"$schema": SCHEMA_ID, "blocks": clean_blocks}


def sync_content_from_body(instance) -> None:
    """
    Keep ``content`` as the HTML projection of ``body`` (version N).

    If ``body`` is empty but ``content`` has HTML, wrap content into body
    (first-write / migration path).
    """
    if not hasattr(instance, "body") or not hasattr(instance, "content"):
        return
    body = getattr(instance, "body", None) or empty_body()
    try:
        body = normalize_body(body)
    except ValueError:
        body = body_from_html(getattr(instance, "content", "") or "")
    html = html_from_body(body)
    content = getattr(instance, "content", "") or ""
    if not html and content.strip():
        body = body_from_html(content)
        html = content
    instance.body = body
    instance.content = html
