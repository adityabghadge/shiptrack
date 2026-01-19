from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from typing import Any

import httpx
from sqlalchemy.orm import Session

from app.db.models import CheckResult, Monitor
from app.services.incident import apply_incident_rules
from app.services.notifier import send_slack

logger = logging.getLogger(__name__)

# Required error types
ERR_TIMEOUT = "TIMEOUT"
ERR_DNS = "DNS"
ERR_CONNECTION = "CONNECTION"
ERR_HTTP_UNEXPECTED = "HTTP_UNEXPECTED"


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _classify_error(exc: Exception) -> tuple[str, str]:
    msg = str(exc)

    if isinstance(exc, httpx.TimeoutException):
        return ERR_TIMEOUT, msg

    if isinstance(exc, httpx.ConnectError):
        low = msg.lower()
        # common DNS substrings across OSes
        if (
            "getaddrinfo" in low
            or "name or service not known" in low
            or "nodename nor servname" in low
        ):
            return ERR_DNS, msg
        return ERR_CONNECTION, msg

    if isinstance(exc, httpx.NetworkError):
        return ERR_CONNECTION, msg

    return ERR_CONNECTION, msg


def _should_retry(exc: Exception) -> bool:
    # Retry only network/timeouts
    return isinstance(exc, (httpx.TimeoutException, httpx.NetworkError, httpx.ConnectError))


def _try_send_slack(event: dict, monitor: Monitor, result: CheckResult) -> None:
    """
    Sends Slack alerts when incidents OPEN/RESOLVE.

    Uses:
    - attachments.color for the nice colored bar
    - blocks for a clean, human-readable layout

    IMPORTANT: Slack webhook payload must include non-empty "text".
    """
    transition = event.get("transition")
    if transition not in ("OPENED", "RESOLVED"):
        return

    incident_id = event.get("incident_id")
    monitor_id = str(monitor.id)
    check_id = str(result.id)

    # Color via attachment
    color = "#E01E5A" if transition == "OPENED" else "#2EB67D"
    title = "🚨 Incident OPENED" if transition == "OPENED" else "✅ Incident RESOLVED"

    observed = result.status_code if result.status_code is not None else "—"
    latency = f"{result.latency_ms} ms" if result.latency_ms is not None else "—"

    # Always non-empty fallback string
    text = f"{title}: {monitor.name} ({monitor.url})"

    blocks: list[dict[str, Any]] = [
        {"type": "header", "text": {"type": "plain_text", "text": title}},
        {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*Monitor:*\n<{monitor.url}|{monitor.name}>"},
                {"type": "mrkdwn", "text": f"*Monitor ID:*\n`{monitor_id}`"},
                {"type": "mrkdwn", "text": f"*Expected:*\n`{monitor.expected_status}`"},
                {"type": "mrkdwn", "text": f"*Observed:*\n`{observed}`"},
                {"type": "mrkdwn", "text": f"*Latency:*\n`{latency}`"},
                {"type": "mrkdwn", "text": f"*Error:*\n`{result.error_type or '—'}`"},
            ],
        },
    ]

    if result.error_message:
        blocks.append(
            {"type": "section", "text": {"type": "mrkdwn", "text": f"*Details:*\n```{result.error_message}```"}}
        )

    blocks.extend(
        [
            {"type": "divider"},
            {
                "type": "context",
                "elements": [
                    {"type": "mrkdwn", "text": f"*Incident:* `{incident_id}`"},
                    {"type": "mrkdwn", "text": f"*Check:* `{check_id}`"},
                    {"type": "mrkdwn", "text": f"*When:* `{result.checked_at.isoformat() if result.checked_at else '—'}`"},
                ],
            },
        ]
    )

    attachments = [{"color": color, "blocks": blocks}]

    logger.info(
        "Slack alert attempt: transition=%s incident_id=%s monitor_id=%s",
        transition,
        incident_id,
        monitor_id,
    )

    ok = send_slack(text, attachments=attachments)
    if not ok:
        logger.warning("Slack send returned false (see notifier logs for status/body)")


def run_check(db: Session, monitor: Monitor) -> CheckResult:
    """
    Strict rules:
    - httpx
    - timeout = monitor.timeout_ms
    - success if status_code == expected_status
    - 3 total attempts
    - backoff: 0.5s -> 1s
    - retry only network/timeouts
    - store final outcome only
    """

    timeout = httpx.Timeout(monitor.timeout_ms / 1000.0)
    headers = monitor.headers_json or {}

    status_code: int | None = None
    latency_ms: int | None = None
    success = False
    error_type: str | None = None
    error_message: str | None = None

    backoffs = [0.0, 0.5, 1.0]  # attempt1 no sleep, attempt2 0.5s, attempt3 1s

    for attempt in range(3):
        if backoffs[attempt] > 0:
            time.sleep(backoffs[attempt])

        start = time.perf_counter()
        try:
            with httpx.Client(timeout=timeout, follow_redirects=True) as client:
                resp = client.request(monitor.method, monitor.url, headers=headers)

            latency_ms = int((time.perf_counter() - start) * 1000)
            status_code = resp.status_code

            if status_code == monitor.expected_status:
                success = True
                error_type = None
                error_message = None
            else:
                success = False
                error_type = ERR_HTTP_UNEXPECTED
                error_message = f"Expected {monitor.expected_status} got {status_code}"

            # Don't retry on HTTP response mismatch
            break

        except Exception as exc:
            latency_ms = int((time.perf_counter() - start) * 1000)

            if _should_retry(exc) and attempt < 2:
                continue

            error_type, error_message = _classify_error(exc)
            success = False
            status_code = None
            break

    result = CheckResult(
        monitor_id=monitor.id,
        checked_at=_now_utc(),
        success=success,
        status_code=status_code,
        latency_ms=latency_ms,
        error_type=error_type,
        error_message=error_message,
    )

    db.add(result)
    db.commit()
    db.refresh(result)

    # Incident transitions (OPEN/RESOLVE) happen here:
    event = apply_incident_rules(db, result)

    # Slack alerts should fire ONLY on OPEN/RESOLVE transitions:
    _try_send_slack(event, monitor, result)

    return result