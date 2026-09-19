"""Event ingestion request and response schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from app.domain.enums import EventSource, EventType


class EventIngestRequest(BaseModel):
    """Payload for submitting a single security event."""

    event_id: UUID | None = None
    occurred_at: datetime | None = None
    source: EventSource = EventSource.SIMULATOR
    event_type: EventType = EventType.LOGIN_FAILED
    host: str | None = None
    username: str | None = None
    src_ip: str | None = None
    dst_ip: str | None = None
    dst_port: int | None = Field(default=None, ge=1, le=65535)
    process_name: str | None = None
    command_line: str | None = None
    file_path: str | None = None
    file_hash_sha256: str | None = Field(default=None, min_length=64, max_length=64)
    bytes_out: int | None = Field(default=None, ge=0)
    http_path: str | None = None
    severity_hint: int | None = Field(default=None, ge=0, le=10)
    raw: dict[str, Any] = Field(default_factory=dict)


class BatchEventIngestRequest(BaseModel):
    """Payload for submitting up to 500 security events at once."""

    events: list[EventIngestRequest] = Field(..., min_length=1, max_length=500)


class IngestResponse(BaseModel):
    """Result of an ingestion request."""

    accepted_count: int
    event_ids: list[UUID]
    status: str = "accepted"


class EventResponse(BaseModel):
    """Detailed event representation returned by query endpoints."""

    event_id: UUID
    occurred_at: datetime
    ingested_at: datetime
    source: EventSource
    event_type: EventType
    host: str | None
    username: str | None
    src_ip: str | None
    dst_ip: str | None
    dst_port: int | None
    process_name: str | None
    command_line: str | None
    file_path: str | None
    file_hash_sha256: str | None
    bytes_out: int | None
    http_path: str | None
    severity_hint: int | None
    raw: dict[str, Any]
