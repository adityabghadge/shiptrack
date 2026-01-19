from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
import statistics

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.db.models import Monitor, CheckResult, Incident
from app.schemas.monitor import MonitorCreate, MonitorUpdate


# ----------------------------
# Monitors
# ----------------------------
def create_monitor(db: Session, data: MonitorCreate) -> Monitor:
    monitor = Monitor(
        name=data.name,
        url=str(data.url),
        method=data.method,
        expected_status=data.expected_status,
        interval_sec=data.interval_sec,
        timeout_ms=data.timeout_ms,
        is_active=data.is_active,
        headers_json=data.headers_json,
    )
    db.add(monitor)
    db.commit()
    db.refresh(monitor)
    return monitor


def list_monitors(db: Session) -> list[Monitor]:
    return db.query(Monitor).order_by(Monitor.created_at.desc()).all()


def get_monitor(db: Session, monitor_id: uuid.UUID) -> Monitor | None:
    return db.query(Monitor).filter(Monitor.id == monitor_id).first()


def update_monitor(db: Session, monitor: Monitor, data: MonitorUpdate) -> Monitor:
    update_data = data.model_dump(exclude_unset=True)

    # IMPORTANT: Pydantic HttpUrl must be converted to string for SQLAlchemy/psycopg
    if "url" in update_data and update_data["url"] is not None:
        update_data["url"] = str(update_data["url"])

    for field, value in update_data.items():
        setattr(monitor, field, value)

    db.add(monitor)
    db.commit()
    db.refresh(monitor)
    return monitor


def soft_delete_monitor(db: Session, monitor: Monitor) -> Monitor:
    monitor.is_active = False
    db.add(monitor)
    db.commit()
    db.refresh(monitor)
    return monitor


# ----------------------------
# Check Results
# ----------------------------
def list_results_for_monitor(db: Session, monitor_id: uuid.UUID, limit: int = 100) -> list[CheckResult]:
    limit = max(1, min(limit, 500))
    return (
        db.query(CheckResult)
        .filter(CheckResult.monitor_id == monitor_id)
        .order_by(CheckResult.checked_at.desc())
        .limit(limit)
        .all()
    )


# ----------------------------
# Incidents
# ----------------------------
def list_incidents(db: Session, status: str | None = None, limit: int = 100) -> list[Incident]:
    """
    List incidents, optionally filtered by status (OPEN/RESOLVED).
    """
    limit = max(1, min(limit, 500))
    q = db.query(Incident)

    if status:
        status_up = status.strip().upper()
        if status_up not in {"OPEN", "RESOLVED"}:
            raise HTTPException(status_code=400, detail="status must be OPEN or RESOLVED")
        q = q.filter(Incident.status == status_up)

    return q.order_by(Incident.started_at.desc()).limit(limit).all()


def list_incidents_for_monitor(
    db: Session, monitor_id: uuid.UUID, limit: int = 100
) -> list[Incident]:
    """
    List incidents for a specific monitor.
    """
    limit = max(1, min(limit, 500))
    return (
        db.query(Incident)
        .filter(Incident.monitor_id == monitor_id)
        .order_by(Incident.started_at.desc())
        .limit(limit)
        .all()
    )


def get_open_incident(db: Session, monitor_id: uuid.UUID) -> Incident | None:
    """
    Helper for incident state machine: one OPEN incident per monitor.
    """
    return (
        db.query(Incident)
        .filter(Incident.monitor_id == monitor_id)
        .filter(Incident.status == "OPEN")
        .order_by(Incident.started_at.desc())
        .first()
    )


# ----------------------------
# Summary
# ----------------------------
def _parse_window(window: str) -> timedelta:
    """
    Supports: '24h', '7d', '60m'
    """
    window = window.strip().lower()
    if window.endswith("h"):
        return timedelta(hours=int(window[:-1]))
    if window.endswith("d"):
        return timedelta(days=int(window[:-1]))
    if window.endswith("m"):
        return timedelta(minutes=int(window[:-1]))
    raise ValueError("Invalid window format. Use like 24h, 7d, 60m")


def get_monitor_summary(db: Session, monitor_id: uuid.UUID, window: str = "24h") -> dict:
    try:
        delta = _parse_window(window)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid window. Use like 24h, 7d, 60m")

    since = datetime.now(timezone.utc) - delta

    results = (
        db.query(CheckResult)
        .filter(CheckResult.monitor_id == monitor_id)
        .filter(CheckResult.checked_at >= since)
        .order_by(CheckResult.checked_at.desc())
        .all()
    )

    total_checks = len(results)
    success_checks = sum(1 for r in results if r.success)

    uptime_percent = round((success_checks / total_checks) * 100, 2) if total_checks > 0 else 0.0

    latencies = [r.latency_ms for r in results if r.latency_ms is not None]
    avg_latency_ms = round(sum(latencies) / len(latencies), 2) if latencies else None
    median_latency_ms = statistics.median(latencies) if latencies else None

    current_status = "UP"
    if results:
        current_status = "UP" if results[0].success else "DOWN"

    return {
        "monitor_id": str(monitor_id),
        "window": window,
        "uptime_percent": uptime_percent,
        "total_checks": total_checks,
        "success_checks": success_checks,
        "avg_latency_ms": avg_latency_ms,
        "median_latency_ms": median_latency_ms,
        "current_status": current_status,
    }