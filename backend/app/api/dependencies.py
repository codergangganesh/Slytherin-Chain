"""FastAPI dependency injection utilities for authentication, RBAC, and DB sessions."""

from __future__ import annotations

from collections.abc import Callable
from typing import Annotated
from uuid import UUID

from fastapi import Depends, Header, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import get_settings
from app.db.session import get_db_session
from app.domain.enums import UserRole
from app.domain.exceptions import AuthenticationError
from app.domain.user import User
from app.repositories.user_repository import UserRepository
from app.services.auth_service import decode_token, hash_api_key

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Security(bearer_scheme)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> User:
    """Extract and validate the JWT token, returning the authenticated User."""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": {"code": "AUTHENTICATION_REQUIRED", "message": "Missing Bearer token"}
            },
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = decode_token(credentials.credentials, expected_type="access")
        user_id_str = payload.get("sub")
        if not user_id_str:
            raise AuthenticationError("Token payload missing subject")
        user_id = UUID(user_id_str)
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"code": "INVALID_TOKEN", "message": str(err)}},
            headers={"WWW-Authenticate": "Bearer"},
        ) from err

    user_repo = UserRepository(session)
    user = await user_repo.get_by_id(user_id)
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"code": "USER_NOT_FOUND", "message": "User not found or inactive"}},
        )
    return user


ROLE_HIERARCHY: dict[UserRole, int] = {
    UserRole.VIEWER: 1,
    UserRole.ANALYST: 2,
    UserRole.ADMIN: 3,
}


def require_role(min_role: UserRole) -> Callable[[User], User]:
    """Dependency factory enforcing minimum required role hierarchy."""

    def role_checker(current_user: Annotated[User, Depends(get_current_user)]) -> User:
        user_level = ROLE_HIERARCHY.get(current_user.role, 0)
        required_level = ROLE_HIERARCHY.get(min_role, 99)
        if user_level < required_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": {
                        "code": "INSUFFICIENT_PERMISSIONS",
                        "message": f"Action requires at least '{min_role.value}' role.",
                    }
                },
            )
        return current_user

    return role_checker


require_viewer = require_role(UserRole.VIEWER)
require_analyst = require_role(UserRole.ANALYST)
require_admin = require_role(UserRole.ADMIN)


async def verify_ingestion_api_key(
    x_api_key: Annotated[str | None, Header(alias="X-API-Key")] = None,
) -> str:
    """Validate the ingestion API key passed via X-API-Key header."""
    settings = get_settings()
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"code": "API_KEY_REQUIRED", "message": "Missing X-API-Key header"}},
        )

    # Fast-path check against configured ingestion key or hash comparison
    if x_api_key != settings.ingestion_api_key:
        expected_hash = hash_api_key(settings.ingestion_api_key)
        provided_hash = hash_api_key(x_api_key)
        if provided_hash != expected_hash:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error": {"code": "INVALID_API_KEY", "message": "Invalid ingestion API key"}
                },
            )
    return x_api_key
