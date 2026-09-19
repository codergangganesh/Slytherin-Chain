"""Asset context enrichment service."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.enums import AssetEnvironment
from app.repositories.asset_repository import AssetRepository


@dataclass(frozen=True)
class AssetContext:
    """Enriched asset context and criticality details."""

    asset_id: UUID | None
    hostname: str
    criticality: int  # 1 - 5
    environment: AssetEnvironment
    is_protected: bool
    is_internet_facing: bool
    exposure_score: float  # 1.0 (internet), 0.5 (internal), 0.2 (isolated)
    is_known: bool


class AssetContextService:
    """Provides asset posture and criticality context for risk scoring."""

    def __init__(self, session: AsyncSession) -> None:
        self._repo = AssetRepository(session)

    async def get_context_by_host(self, host: str | None) -> AssetContext:
        """Resolve asset context from hostname with conservative fallback."""
        if not host:
            return AssetContext(
                asset_id=None,
                hostname="unknown",
                criticality=3,
                environment=AssetEnvironment.PRODUCTION,
                is_protected=False,
                is_internet_facing=False,
                exposure_score=0.5,
                is_known=False,
            )

        asset = await self._repo.get_by_hostname(host)
        if asset:
            exposure = 1.0 if asset.is_internet_facing else 0.5
            return AssetContext(
                asset_id=asset.id,
                hostname=asset.hostname,
                criticality=asset.criticality,
                environment=asset.environment,
                is_protected=asset.is_protected,
                is_internet_facing=asset.is_internet_facing,
                exposure_score=exposure,
                is_known=True,
            )

        # Fallback for unknown asset
        return AssetContext(
            asset_id=None,
            hostname=host,
            criticality=3,
            environment=AssetEnvironment.PRODUCTION,
            is_protected=False,
            is_internet_facing=False,
            exposure_score=0.5,
            is_known=False,
        )

    async def get_context_by_ip(self, ip_address: str | None) -> AssetContext:
        """Resolve asset context from IP address."""
        if not ip_address:
            return await self.get_context_by_host(None)

        asset = await self._repo.get_by_ip(ip_address)
        if asset:
            exposure = 1.0 if asset.is_internet_facing else 0.5
            return AssetContext(
                asset_id=asset.id,
                hostname=asset.hostname,
                criticality=asset.criticality,
                environment=asset.environment,
                is_protected=asset.is_protected,
                is_internet_facing=asset.is_internet_facing,
                exposure_score=exposure,
                is_known=True,
            )
        return await self.get_context_by_host(None)
