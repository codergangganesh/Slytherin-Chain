"""API router for User Authentication and Token Refresh."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.api.schemas.auth_schemas import (
    LoginRequest,
    RefreshTokenRequest,
    TokenResponse,
    UserResponse,
)
from app.config.settings import get_settings
from app.db.session import get_db_session
from app.domain.enums import UserRole
from app.domain.user import User
from app.repositories.user_repository import UserRepository
from app.services.auth_service import (
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=TokenResponse)
async def login(
    payload: LoginRequest,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> TokenResponse:
    """Authenticate with username and password to obtain JWT tokens."""
    settings = get_settings()
    user_repo = UserRepository(session)
    user = await user_repo.get_by_username(payload.username)

    if not user or not user.is_active or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"code": "INVALID_CREDENTIALS", "message": "Invalid username or password"}},
        )

    access_token = create_access_token(user.id, user.username, user.role)
    refresh_token = create_refresh_token(user.id, user.username, user.role)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.access_token_expire_minutes * 60,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    payload: RefreshTokenRequest,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> TokenResponse:
    """Exchange a valid refresh token for a new access and refresh token pair."""
    settings = get_settings()
    try:
        token_data = decode_token(payload.refresh_token, expected_type="refresh")
        user_id_str = token_data.get("sub")
        if not user_id_str:
            raise ValueError("Missing subject")
        user_id = UUID(user_id_str)
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"code": "INVALID_REFRESH_TOKEN", "message": "Refresh token is invalid or expired"}},
        ) from err

    user_repo = UserRepository(session)
    user = await user_repo.get_by_id(user_id)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"code": "USER_NOT_FOUND", "message": "User not found or inactive"}},
        )

    access_token = create_access_token(user.id, user.username, user.role)
    new_refresh_token = create_refresh_token(user.id, user.username, user.role)

    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
        expires_in=settings.access_token_expire_minutes * 60,
    )


@router.get("/me", response_model=UserResponse)
async def get_my_profile(
    current_user: Annotated[User, Depends(get_current_user)],
) -> UserResponse:
    """Retrieve the current authenticated user's profile."""
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        role=current_user.role,
        is_active=current_user.is_active,
        created_at=current_user.created_at,
    )
