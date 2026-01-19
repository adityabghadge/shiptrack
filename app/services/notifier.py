from __future__ import annotations

import logging
import os
from typing import Any

import httpx

logger = logging.getLogger("app.services.notifier")


def _env_bool(name: str, default: bool = False) -> bool:
    val = os.getenv(name, str(default)).strip().lower()
    return val in {"1", "true", "yes", "y", "on"}


def send_slack(
    text: str,
    *,
    blocks: list[dict[str, Any]] | None = None,
    attachments: list[dict[str, Any]] | None = None,
) -> bool:
    enabled = _env_bool("SLACK_ALERTS_ENABLED", False)
    url = os.getenv("SLACK_WEBHOOK_URL", "").strip()

    if not enabled:
        logger.warning("Slack disabled (SLACK_ALERTS_ENABLED=false)")
        return False
    if not url:
        logger.error("Slack webhook missing (SLACK_WEBHOOK_URL empty)")
        return False

    # Slack requires "text" for some payloads; keep it always.
    payload: dict[str, Any] = {"text": text}

    if blocks:
        payload["blocks"] = blocks
    if attachments:
        payload["attachments"] = attachments

    try:
        resp = httpx.post(url, json=payload, timeout=10.0)
        logger.info("Slack response: status=%s body=%s", resp.status_code, resp.text.strip()[:200])
        return 200 <= resp.status_code < 300
    except Exception:
        logger.exception("Slack send failed")
        return False