from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.session import Base


class Monitor(Base):
    __tablename__ = "monitors"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    name = Column(String(255), nullable=False)
    url = Column(String(2048), nullable=False)
    method = Column(String(10), nullable=False, default="GET")
    expected_status = Column(Integer, nullable=False, default=200)

    interval_sec = Column(Integer, nullable=False, default=60)
    timeout_ms = Column(Integer, nullable=False, default=3000)

    is_active = Column(Boolean, nullable=False, default=True)
    headers_json = Column(JSON, nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    results = relationship("CheckResult", back_populates="monitor", cascade="all, delete-orphan")
    incidents = relationship("Incident", back_populates="monitor", cascade="all, delete-orphan")


class CheckResult(Base):
    __tablename__ = "check_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    monitor_id = Column(
        UUID(as_uuid=True),
        ForeignKey("monitors.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    checked_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )

    success = Column(Boolean, nullable=False)
    status_code = Column(Integer, nullable=True)
    latency_ms = Column(Integer, nullable=True)

    error_type = Column(String(32), nullable=True)
    error_message = Column(String(1024), nullable=True)

    monitor = relationship("Monitor", back_populates="results")


class Incident(Base):
    __tablename__ = "incidents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    monitor_id = Column(
        UUID(as_uuid=True),
        ForeignKey("monitors.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    status = Column(String(20), nullable=False, default="OPEN")  # OPEN / RESOLVED
    started_at = Column(DateTime(timezone=True), nullable=False)
    last_failure_at = Column(DateTime(timezone=True), nullable=False)
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    failure_count = Column(Integer, nullable=False, default=0)
    last_error_type = Column(String(50), nullable=True)
    last_error_message = Column(Text, nullable=True)

    monitor = relationship("Monitor", back_populates="incidents")