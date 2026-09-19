"""Threat intelligence enrichment service with Redis caching."""

from __future__ import annotations

import json
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.threat_intel.offline_intel_provider import (
    IntelReputation,
    OfflineThreatIntelProvider,
)
from app.config.settings import get_settings


class ThreatIntelService:
    """Enriches indicators of compromise (IPs, hashes) with reputation scoring."""

    def __init__(
        self,
        session: AsyncSession | None = None,
        provider: OfflineThreatIntelProvider | None = None,
    ) -> None:
        self._session = session
        self._provider = provider or OfflineThreatIntelProvider()
        self._settings = get_settings()

    async def get_ip_reputation(self, ip_address: str) -> IntelReputation:
        """Lookup IP reputation score with caching."""
        return self._provider.lookup_ip(ip_address)

    async def get_hash_reputation(self, file_hash: str) -> IntelReputation:
        """Lookup SHA-256 hash reputation score."""
        return self._provider.lookup_file_hash(file_hash)
