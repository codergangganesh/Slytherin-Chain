"""Domain model for API Keys used for ingestion authentication."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class ApiKey:
    """Represents a hashed API key for machine-to-machine ingestion authentication."""

    id: UUID
    name: str
    key_hash: str
    prefix: str
    is_active: bool
    created_at: datetime
    last_used_at: datetime | None = None
