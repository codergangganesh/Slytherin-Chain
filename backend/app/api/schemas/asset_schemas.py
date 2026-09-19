"""Asset inventory request and response schemas."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.domain.enums import AssetEnvironment


class AssetCreateRequest(BaseModel):
    """Payload to create a new managed asset."""

    hostname: str = Field(..., min_length=1, max_length=128)
    ip_address: str = Field(..., min_length=7, max_length=64)
    criticality: int = Field(default=3, ge=1, le=5)
    environment: AssetEnvironment = Field(default=AssetEnvironment.PRODUCTION)
    is_protected: bool = Field(default=False)
    is_internet_facing: bool = Field(default=False)
    owner: str = Field(default="Security Ops", max_length=128)
    tags: list[str] = Field(default_factory=list)


class AssetUpdateRequest(BaseModel):
    """Payload to update an existing asset."""

    criticality: int | None = Field(default=None, ge=1, le=5)
    environment: AssetEnvironment | None = None
    is_protected: bool | None = None
    is_internet_facing: bool | None = None
    owner: str | None = Field(default=None, max_length=128)
    tags: list[str] | None = None


class AssetResponse(BaseModel):
    """Managed asset details response."""

    id: UUID
    hostname: str
    ip_address: str
    criticality: int
    environment: AssetEnvironment
    is_protected: bool
    is_internet_facing: bool
    owner: str
    tags: list[str]
    created_at: datetime
    updated_at: datetime
