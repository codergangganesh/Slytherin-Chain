"""Domain model for Normalized Security Events.

Follows the schema defined in MASTER_PROMPT Section 8.1.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID

from app.domain.enums import EventSource, EventType


@dataclass(frozen=True)
class NormalizedEvent:
    """Represents a normalized security event formatted for processing and detection."""

    event_id: UUID
    occurred_at: datetime
    ingested_at: datetime
    source: EventSource
    event_type: EventType
    host: str | None = None
    username: str | None = None
    src_ip: str | None = None
    dst_ip: str | None = None
    dst_port: int | None = None
    process_name: str | None = None
    command_line: str | None = None
    file_path: str | None = None
    file_hash_sha256: str | None = None
    bytes_out: int | None = None
    http_path: str | None = None
    severity_hint: int | None = None
    raw: dict[str, Any] = field(default_factory=dict)
