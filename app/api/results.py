from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db import crud
from app.db.session import get_db
from app.schemas.result import CheckResultOut

router = APIRouter(prefix="/monitors", tags=["results"])


@router.get("/{monitor_id}/results", response_model=list[CheckResultOut])
def get_results(
    monitor_id: uuid.UUID,
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    monitor = crud.get_monitor(db, monitor_id)
    if not monitor:
        raise HTTPException(status_code=404, detail="Monitor not found")

    return crud.list_results_for_monitor(db, monitor_id, limit=limit)

@router.get("/{monitor_id}/summary")
def get_summary(
    monitor_id: uuid.UUID,
    window: str = "24h",
    db: Session = Depends(get_db),
):
    monitor = crud.get_monitor(db, monitor_id)
    if not monitor:
        raise HTTPException(status_code=404, detail="Monitor not found")

    return crud.get_monitor_summary(db, monitor_id, window=window)