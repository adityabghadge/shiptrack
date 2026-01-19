from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class IncidentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    monitor_id: uuid.UUID

    status: str  # OPEN / RESOLVED

    started_at: datetime
    last_failure_at: datetime
    resolved_at: datetime | None

    failure_count: int
    last_error_type: str | None
    last_error_message: str | None