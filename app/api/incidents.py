from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db import crud
from app.db.session import get_db
from app.schemas.incident import IncidentOut

router = APIRouter(tags=["incidents"])


@router.get("/incidents", response_model=list[IncidentOut])
def get_incidents(
    status: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    if status is not None:
        status = status.strip().upper()
        if status not in {"OPEN", "RESOLVED"}:
            raise HTTPException(status_code=400, detail="status must be OPEN or RESOLVED")

    return crud.list_incidents(db, status=status, limit=limit)


@router.get("/monitors/{monitor_id}/incidents", response_model=list[IncidentOut])
def get_monitor_incidents(
    monitor_id: uuid.UUID,
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    monitor = crud.get_monitor(db, monitor_id)
    if not monitor:
        raise HTTPException(status_code=404, detail="Monitor not found")

    return crud.list_incidents_for_monitor(db, monitor_id, limit=limit)