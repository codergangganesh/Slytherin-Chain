"""Domain model for Users."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.domain.enums import UserRole


@dataclass(frozen=True)
class User:
    """Represents an authenticated user in the system."""

    id: UUID
    username: str
    email: str
    password_hash: str
    role: UserRole
    is_active: bool
    created_at: datetime
    updated_at: datetime
