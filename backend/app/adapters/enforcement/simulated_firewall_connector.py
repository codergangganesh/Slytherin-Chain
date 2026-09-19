"""Simulated firewall connector writing to blocklist_entries table."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.enforcement.enforcement_connector import EnforcementConnector
from app.db.orm_models import BlocklistEntryOrm
from app.domain.enums import ActionType


class SimulatedFirewallConnector(EnforcementConnector):
    """Simulated firewall connector managing virtual IP blocking."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def supports_action(self, action_type: ActionType) -> bool:
        return action_type in (ActionType.BLOCK_IP,)

    async def validate(self, target: str, parameters: dict[str, Any]) -> tuple[bool, str]:
        if not target or "." not in target:
            return False, f"Invalid IPv4 target: {target}"
        return True, "Valid IP address"

    async def dry_run(self, target: str, parameters: dict[str, Any]) -> dict[str, Any]:
        return {
            "mode": "dry_run",
            "connector": "SimulatedFirewall",
            "effect": f"Would add {target} to firewall DROP rules",
            "simulated_rule_id": f"fw_drop_{target.replace('.', '_')}",
        }

    async def execute(
        self,
        action_id: UUID,
        incident_id: UUID,
        target: str,
        parameters: dict[str, Any],
        ttl_seconds: int | None = None,
    ) -> dict[str, Any]:
        now = datetime.now(UTC)
        expires_at = now + timedelta(seconds=ttl_seconds) if ttl_seconds else None

        stmt = select(BlocklistEntryOrm).where(BlocklistEntryOrm.ip_address == target)
        res = await self._session.execute(stmt)
        existing = res.scalar_one_or_none()

        if existing:
            existing.is_active = True
            existing.expires_at = expires_at
            existing.action_id = action_id
            existing.incident_id = incident_id
        else:
            orm = BlocklistEntryOrm(
                ip_address=target,
                reason=str(parameters.get("reason", "Autonomous threat block")),
                incident_id=incident_id,
                action_id=action_id,
                created_at=now,
                expires_at=expires_at,
                is_active=True,
            )
            self._session.add(orm)

        await self._session.flush()
        return {
            "status": "success",
            "connector": "SimulatedFirewall",
            "action": "BLOCK_IP",
            "ip_address": target,
            "rule": f"DROP all from {target}",
            "expires_at": expires_at.isoformat() if expires_at else None,
        }

    async def rollback(
        self,
        action_id: UUID,
        target: str,
        parameters: dict[str, Any],
    ) -> dict[str, Any]:
        stmt = (
            update(BlocklistEntryOrm)
            .where(BlocklistEntryOrm.ip_address == target)
            .values(is_active=False)
        )
        await self._session.execute(stmt)
        await self._session.flush()
        return {
            "status": "rolled_back",
            "connector": "SimulatedFirewall",
            "action": "UNBLOCK_IP",
            "ip_address": target,
        }
