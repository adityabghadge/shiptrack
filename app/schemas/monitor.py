from __future__ import annotations

import uuid


from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, HttpUrl
from pydantic import ConfigDict


class MonitorCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    url: HttpUrl
    method: str = Field(default="GET", max_length=10)
    expected_status: int = Field(default=200, ge=100, le=599)
    interval_sec: int = Field(default=60, ge=5, le=86400)
    timeout_ms: int = Field(default=3000, ge=100, le=60000)
    is_active: bool = True
    headers_json: dict[str, Any] | None = None


class MonitorUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    url: HttpUrl | None = None
    method: str | None = Field(default=None, max_length=10)
    expected_status: int | None = Field(default=None, ge=100, le=599)
    interval_sec: int | None = Field(default=None, ge=5, le=86400)
    timeout_ms: int | None = Field(default=None, ge=100, le=60000)
    is_active: bool | None = None
    headers_json: dict[str, Any] | None = None


class MonitorOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    url: str
    method: str
    expected_status: int
    interval_sec: int
    timeout_ms: int
    is_active: bool
    headers_json: dict[str, Any] | None
    created_at: datetime
    updated_at: datetime

