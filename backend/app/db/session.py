"""Database session management with SQLAlchemy 2.0 AsyncEngine.

Supports connection pooling and async context management for FastAPI.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Any

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.config.settings import get_settings


class Base(DeclarativeBase):
    """Base declarative class for all SQLAlchemy ORM models."""

    pass


_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def get_engine() -> AsyncEngine:
    """Retrieve or lazily initialize the AsyncEngine instance."""
    global _engine
    if _engine is None:
        settings = get_settings()
        connect_args: dict[str, Any] = {}
        if "sqlite" in settings.database_url:
            connect_args["check_same_thread"] = False
        _engine = create_async_engine(
            settings.database_url,
            echo=False,
            future=True,
            connect_args=connect_args,
        )
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Retrieve or lazily initialize the sessionmaker."""
    global _session_factory
    if _session_factory is None:
        engine = get_engine()
        _session_factory = async_sessionmaker(
            bind=engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )
    return _session_factory


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for yielding an asynchronous database session."""
    session_factory = get_session_factory()
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
