from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.security import require_api_key
from app.db import crud
from app.db.models import Monitor
from app.db.session import get_db
from app.schemas.monitor import MonitorCreate, MonitorOut, MonitorUpdate
from app.schemas.result import CheckResultOut
from app.services.checker import run_check

router = APIRouter(prefix="/monitors", tags=["monitors"])


@router.get(
    "",
    response_model=list[MonitorOut],
    dependencies=[Depends(require_api_key)],
)
def list_monitors(db: Session = Depends(get_db)):
    return crud.list_monitors(db)


@router.post(
    "",
    response_model=MonitorOut,
    dependencies=[Depends(require_api_key)],
)
def create_monitor(payload: MonitorCreate, db: Session = Depends(get_db)):
    return crud.create_monitor(db, payload)


@router.get(
    "/{monitor_id}",
    response_model=MonitorOut,
    dependencies=[Depends(require_api_key)],
)
def get_monitor(monitor_id: uuid.UUID, db: Session = Depends(get_db)):
    monitor = crud.get_monitor(db, monitor_id)
    if not monitor:
        raise HTTPException(status_code=404, detail="Monitor not found")
    return monitor


@router.patch(
    "/{monitor_id}",
    response_model=MonitorOut,
    dependencies=[Depends(require_api_key)],
)
def update_monitor(
    monitor_id: uuid.UUID,
    payload: MonitorUpdate,
    db: Session = Depends(get_db),
):
    monitor = crud.get_monitor(db, monitor_id)
    if not monitor:
        raise HTTPException(status_code=404, detail="Monitor not found")
    return crud.update_monitor(db, monitor, payload)


@router.delete(
    "/{monitor_id}",
    response_model=MonitorOut,
    dependencies=[Depends(require_api_key)],
)
def delete_monitor(monitor_id: uuid.UUID, db: Session = Depends(get_db)):
    monitor = crud.get_monitor(db, monitor_id)
    if not monitor:
        raise HTTPException(status_code=404, detail="Monitor not found")
    return crud.soft_delete_monitor(db, monitor)


@router.post(
    "/{monitor_id}/check-now",
    response_model=CheckResultOut,
    dependencies=[Depends(require_api_key)],
)
def check_now(monitor_id: uuid.UUID, db: Session = Depends(get_db)):
    monitor = db.get(Monitor, monitor_id)
    if not monitor:
        raise HTTPException(status_code=404, detail="Monitor not found")

    if not monitor.is_active:
        raise HTTPException(status_code=400, detail="Monitor is inactive")

    return run_check(db, monitor)