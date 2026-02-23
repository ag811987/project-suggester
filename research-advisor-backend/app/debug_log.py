"""Minimal NDJSON debug logger for Cursor debug mode.

Writes one JSON object per line to the provisioned debug log path.
Never log secrets or user-provided research content.
"""

from __future__ import annotations

import json
import time
from typing import Any

_DEBUG_LOG_PATH = "/Users/amit/Coding-Projects/Project-Suggester/.cursor/debug.log"


def debug_log(
    *,
    location: str,
    message: str,
    data: dict[str, Any],
    run_id: str,
    hypothesis_id: str,
) -> None:
    # region agent log
    payload = {
        "id": f"log_{time.time_ns()}",
        "timestamp": int(time.time() * 1000),
        "location": location,
        "message": message,
        "data": data,
        "runId": run_id,
        "hypothesisId": hypothesis_id,
    }
    try:
        with open(_DEBUG_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False) + "\n")
    except Exception:
        pass
    # endregion
