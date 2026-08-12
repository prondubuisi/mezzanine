"""Structured JSON logging helpers (PR-036b)."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any


def structured_log(
    logger: logging.Logger,
    level: int,
    event: str,
    **fields: Any,
) -> None:
    """Emit one JSON log line: ``{"ts", "event", ...fields}``."""
    payload = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "event": event,
        **fields,
    }
    logger.log(level, json.dumps(payload, default=str, ensure_ascii=False))
