"""Simulated identity and host isolation connector."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.enforcement.enforcement_connector import EnforcementConnector
from app.db.orm_models import DisabledUserOrm, QuarantinedHostOrm
from app.domain.enums import ActionType


class SimulatedIdentityConnector(EnforcementConnector):
    """Simulates endpoint isolation, user suspension, and access restrictions."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def supports_action(self, action_type: ActionType) -> bool:
        return action_type in (
            ActionType.ISOLATE_HOST,
            ActionType.DISABLE_USER,
            ActionType.RESTRICT_ACCESS,
            ActionType.NOTIFY,
        )

    async def validate(self, target: str, parameters: dict[str, Any]) -> tuple[bool, str]:
        if not target or not target.strip():
            return False, "Target identifier cannot be empty"
        return True, "Target valid"

    async def dry_run(self, target: str, parameters: dict[str, Any]) -> dict[str, Any]:
        return {
            "mode": "dry_run",
            "connector": "SimulatedIdentity",
            "effect": f"Would apply restriction/isolation on target '{target}'",
        }

    async def execute(
        self,
        action_id: UUID,
        incident_id: UUID,
        target: str,
        parameters: dict[str, Any],
        ttl_seconds: int | None = None,
    ) -> dict[str, Any]:
        now = datetime.now(timezone.utc)
        action_type = str(parameters.get("action_type", "isolate_host"))

        if action_type == ActionType.ISOLATE_HOST.value:
            stmt = select(QuarantinedHostOrm).where(QuarantinedHostOrm.hostname == target)
            res = await self._session.execute(stmt)
            existing = res.scalar_one_or_none()
            if existing:
                existing.is_active = True
                existing.action_id = action_id
                existing.incident_id = incident_id
            else:
                orm = QuarantinedHostOrm(
                    hostname=target,
                    reason=str(parameters.get("reason", "Host quarantined due to threat activity")),
                    incident_id=incident_id,
                    action_id=action_id,
                    created_at=now,
                    is_active=True,
                )
                self._session.add(orm)

        elif action_type in (ActionType.DISABLE_USER.value, ActionType.RESTRICT_ACCESS.value):
            stmt = select(DisabledUserOrm).where(DisabledUserOrm.username == target)
            res = await self._session.execute(stmt)
            existing_user = res.scalar_one_or_none()
            if existing_user:
                existing_user.is_active = True
                existing_user.action_id = action_id
                existing_user.incident_id = incident_id
            else:
                user_orm = DisabledUserOrm(
                    username=target,
                    reason=str(parameters.get("reason", "Account disabled / restricted")),
                    incident_id=incident_id,
                    action_id=action_id,
                    created_at=now,
                    is_active=True,
                )
                self._session.add(user_orm)

        await self._session.flush()
        return {
            "status": "success",
            "connector": "SimulatedIdentity",
            "action": action_type,
            "target": target,
        }

    async def rollback(
        self,
        action_id: UUID,
        target: str,
        parameters: dict[str, Any],
    ) -> dict[str, Any]:
        action_type = str(parameters.get("action_type", "isolate_host"))
        if action_type == ActionType.ISOLATE_HOST.value:
            stmt = (
                update(QuarantinedHostOrm)
                .where(QuarantinedHostOrm.hostname == target)
                .values(is_active=False)
            )
            await self._session.execute(stmt)
        elif action_type in (ActionType.DISABLE_USER.value, ActionType.RESTRICT_ACCESS.value):
            stmt2 = (
                update(DisabledUserOrm)
                .where(DisabledUserOrm.username == target)
                .values(is_active=False)
            )
            await self._session.execute(stmt2)

        await self._session.flush()
        return {
            "status": "rolled_back",
            "connector": "SimulatedIdentity",
            "action": f"REVERT_{action_type.upper()}",
            "target": target,
        }
