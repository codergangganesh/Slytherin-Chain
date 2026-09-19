"""Authentication and token request/response schemas."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field

from app.domain.enums import UserRole


class LoginRequest(BaseModel):
    """User credentials login payload."""

    username: str = Field(..., min_length=3, max_length=64)
    password: str = Field(..., min_length=6)


class RefreshTokenRequest(BaseModel):
    """JWT refresh token exchange payload."""

    refresh_token: str


class TokenResponse(BaseModel):
    """JWT bearer token response."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class UserResponse(BaseModel):
    """Authenticated user profile representation."""

    id: UUID
    username: str
    email: str
    role: UserRole
    is_active: bool
    created_at: datetime
