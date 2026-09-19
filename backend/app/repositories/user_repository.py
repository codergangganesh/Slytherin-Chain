"""Repository for User data access."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.orm_models import UserOrm
from app.domain.enums import UserRole
from app.domain.user import User


class UserRepository:
    """Encapsulates all database operations for User entities."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @staticmethod
    def _to_domain(orm: UserOrm) -> User:
        """Convert ORM model to domain model."""
        return User(
            id=orm.id,
            username=orm.username,
            email=orm.email,
            password_hash=orm.password_hash,
            role=UserRole(orm.role),
            is_active=orm.is_active,
            created_at=orm.created_at,
            updated_at=orm.updated_at,
        )

    async def get_by_id(self, user_id: UUID) -> User | None:
        """Retrieve a user by unique UUID."""
        stmt = select(UserOrm).where(UserOrm.id == user_id)
        result = await self._session.execute(stmt)
        orm = result.scalar_one_or_none()
        return self._to_domain(orm) if orm else None

    async def get_by_username(self, username: str) -> User | None:
        """Retrieve a user by unique username."""
        stmt = select(UserOrm).where(UserOrm.username == username)
        result = await self._session.execute(stmt)
        orm = result.scalar_one_or_none()
        return self._to_domain(orm) if orm else None

    async def get_by_email(self, email: str) -> User | None:
        """Retrieve a user by unique email."""
        stmt = select(UserOrm).where(UserOrm.email == email)
        result = await self._session.execute(stmt)
        orm = result.scalar_one_or_none()
        return self._to_domain(orm) if orm else None

    async def create(
        self,
        username: str,
        email: str,
        password_hash: str,
        role: UserRole = UserRole.VIEWER,
        is_active: bool = True,
    ) -> User:
        """Persist a new user account."""
        orm = UserOrm(
            username=username,
            email=email,
            password_hash=password_hash,
            role=role,
            is_active=is_active,
        )
        self._session.add(orm)
        await self._session.flush()
        await self._session.refresh(orm)
        return self._to_domain(orm)

    async def list_users(self, limit: int = 100, offset: int = 0) -> list[User]:
        """List users with pagination."""
        stmt = select(UserOrm).order_by(UserOrm.created_at.desc()).limit(limit).offset(offset)
        result = await self._session.execute(stmt)
        return [self._to_domain(orm) for orm in result.scalars().all()]
