"""Repository for Asset inventory data access."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.orm_models import AssetOrm
from app.domain.asset import Asset
from app.domain.enums import AssetEnvironment


class AssetRepository:
    """Encapsulates all database operations for Asset entities."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @staticmethod
    def _to_domain(orm: AssetOrm) -> Asset:
        """Convert ORM model to domain entity."""
        return Asset(
            id=orm.id,
            hostname=orm.hostname,
            ip_address=orm.ip_address,
            criticality=orm.criticality,
            environment=AssetEnvironment(orm.environment),
            is_protected=orm.is_protected,
            is_internet_facing=orm.is_internet_facing,
            owner=orm.owner,
            tags=list(orm.tags) if orm.tags else [],
            created_at=orm.created_at,
            updated_at=orm.updated_at,
        )

    async def get_by_id(self, asset_id: UUID) -> Asset | None:
        """Find an asset by its unique UUID."""
        stmt = select(AssetOrm).where(AssetOrm.id == asset_id)
        result = await self._session.execute(stmt)
        orm = result.scalar_one_or_none()
        return self._to_domain(orm) if orm else None

    async def get_by_hostname(self, hostname: str) -> Asset | None:
        """Find an asset by hostname (case-insensitive search)."""
        stmt = select(AssetOrm).where(func.lower(AssetOrm.hostname) == hostname.lower())
        result = await self._session.execute(stmt)
        orm = result.scalar_one_or_none()
        return self._to_domain(orm) if orm else None

    async def get_by_ip(self, ip_address: str) -> Asset | None:
        """Find an asset by its IP address."""
        stmt = select(AssetOrm).where(AssetOrm.ip_address == ip_address)
        result = await self._session.execute(stmt)
        orm = result.scalar_one_or_none()
        return self._to_domain(orm) if orm else None

    async def create(
        self,
        hostname: str,
        ip_address: str,
        criticality: int = 3,
        environment: AssetEnvironment = AssetEnvironment.PRODUCTION,
        is_protected: bool = False,
        is_internet_facing: bool = False,
        owner: str = "Security Ops",
        tags: list[str] | None = None,
    ) -> Asset:
        """Persist a new managed asset."""
        orm = AssetOrm(
            hostname=hostname,
            ip_address=ip_address,
            criticality=criticality,
            environment=environment,
            is_protected=is_protected,
            is_internet_facing=is_internet_facing,
            owner=owner,
            tags=tags or [],
        )
        self._session.add(orm)
        await self._session.flush()
        await self._session.refresh(orm)
        return self._to_domain(orm)

    async def list_assets(
        self,
        criticality: int | None = None,
        is_protected: bool | None = None,
        is_internet_facing: bool | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[Asset], int]:
        """List assets with optional filtering and total count."""
        stmt = select(AssetOrm)
        count_stmt = select(func.count()).select_from(AssetOrm)

        if criticality is not None:
            stmt = stmt.where(AssetOrm.criticality == criticality)
            count_stmt = count_stmt.where(AssetOrm.criticality == criticality)
        if is_protected is not None:
            stmt = stmt.where(AssetOrm.is_protected == is_protected)
            count_stmt = count_stmt.where(AssetOrm.is_protected == is_protected)
        if is_internet_facing is not None:
            stmt = stmt.where(AssetOrm.is_internet_facing == is_internet_facing)
            count_stmt = count_stmt.where(AssetOrm.is_internet_facing == is_internet_facing)

        total = await self._session.scalar(count_stmt) or 0
        result = await self._session.execute(
            stmt.order_by(AssetOrm.criticality.desc(), AssetOrm.hostname.asc()).limit(limit).offset(offset)
        )
        assets = [self._to_domain(orm) for orm in result.scalars().all()]
        return assets, total

    async def update(
        self,
        asset_id: UUID,
        criticality: int | None = None,
        environment: AssetEnvironment | None = None,
        is_protected: bool | None = None,
        is_internet_facing: bool | None = None,
        owner: str | None = None,
        tags: list[str] | None = None,
    ) -> Asset | None:
        """Update fields of an existing asset."""
        stmt = select(AssetOrm).where(AssetOrm.id == asset_id)
        result = await self._session.execute(stmt)
        orm = result.scalar_one_or_none()
        if not orm:
            return None

        if criticality is not None:
            orm.criticality = criticality
        if environment is not None:
            orm.environment = environment
        if is_protected is not None:
            orm.is_protected = is_protected
        if is_internet_facing is not None:
            orm.is_internet_facing = is_internet_facing
        if owner is not None:
            orm.owner = owner
        if tags is not None:
            orm.tags = tags

        await self._session.flush()
        await self._session.refresh(orm)
        return self._to_domain(orm)

    async def delete(self, asset_id: UUID) -> bool:
        """Delete an asset by ID."""
        stmt = delete(AssetOrm).where(AssetOrm.id == asset_id)
        result = await self._session.execute(stmt)
        return (result.rowcount or 0) > 0
