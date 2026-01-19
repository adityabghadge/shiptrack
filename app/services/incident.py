from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.db.models import CheckResult, Incident

DOWN_THRESHOLD = 2
RECOVERY_THRESHOLD = 2


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def get_open_incident(db: Session, monitor_id) -> Optional[Incident]:
    return (
        db.query(Incident)
        .filter(Incident.monitor_id == monitor_id)
        .filter(Incident.status == "OPEN")
        .order_by(Incident.started_at.desc())
        .first()
    )


def count_recent_consecutive(db: Session, monitor_id, success_value: bool, limit: int) -> int:
    """
    Count how many most-recent check_results are consecutively success==success_value.
    Stops early when it hits the opposite value.
    """
    rows = (
        db.query(CheckResult)
        .filter(CheckResult.monitor_id == monitor_id)
        .order_by(CheckResult.checked_at.desc())
        .limit(limit)
        .all()
    )

    count = 0
    for r in rows:
        if r.success == success_value:
            count += 1
        else:
            break
    return count


def apply_incident_rules(db: Session, result: CheckResult) -> dict:
    """
    Apply incident transitions based on latest stored result.

    Return shape (standardized):
      - transition: "OPENED" | "RESOLVED" | None
      - incident_id: str | None
      - event: str (optional legacy label)
    """
    monitor_id = result.monitor_id
    open_incident = get_open_incident(db, monitor_id)

    checked_at = result.checked_at or _now_utc()

    # If no open incident, check if we should OPEN one
    if open_incident is None:
        consecutive_failures = count_recent_consecutive(
            db, monitor_id, success_value=False, limit=DOWN_THRESHOLD
        )

        if consecutive_failures >= DOWN_THRESHOLD:
            inc = Incident(
                monitor_id=monitor_id,
                status="OPEN",
                started_at=checked_at,
                last_failure_at=checked_at,
                resolved_at=None,
                failure_count=consecutive_failures,
                last_error_type=result.error_type,
                last_error_message=result.error_message,
            )
            db.add(inc)
            db.commit()
            db.refresh(inc)
            return {
                "transition": "OPENED",
                "incident_id": str(inc.id),
                "event": "INCIDENT_OPENED",
            }

        return {
            "transition": None,
            "incident_id": None,
            "event": "NO_CHANGE",
        }

    # If there IS an open incident, update + possibly resolve
    if result.success:
        consecutive_success = count_recent_consecutive(
            db, monitor_id, success_value=True, limit=RECOVERY_THRESHOLD
        )

        if consecutive_success >= RECOVERY_THRESHOLD:
            open_incident.status = "RESOLVED"
            open_incident.resolved_at = checked_at
            db.add(open_incident)
            db.commit()
            db.refresh(open_incident)
            return {
                "transition": "RESOLVED",
                "incident_id": str(open_incident.id),
                "event": "INCIDENT_RESOLVED",
            }

        return {
            "transition": None,
            "incident_id": str(open_incident.id),
            "event": "NO_CHANGE",
        }

    # Latest result is a failure and incident already open
    open_incident.last_failure_at = checked_at
    open_incident.failure_count = (open_incident.failure_count or 0) + 1
    open_incident.last_error_type = result.error_type
    open_incident.last_error_message = result.error_message
    db.add(open_incident)
    db.commit()
    db.refresh(open_incident)
    return {
        "transition": None,
        "incident_id": str(open_incident.id),
        "event": "NO_CHANGE",
    }