from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class CheckResultOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    monitor_id: uuid.UUID
    checked_at: datetime

    success: bool
    status_code: int | None
    latency_ms: int | None

    error_type: str | None
    error_message: str | None

from typing import List

class CheckResultListOut(BaseModel):
    results: List[CheckResultOut]