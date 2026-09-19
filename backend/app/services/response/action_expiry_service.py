"""Action TTL expiry service."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.enforcement.simulated_firewall_connector import SimulatedFirewallConnector
from app.adapters.enforcement.simulated_identity_connector import SimulatedIdentityConnector
from app.domain.enums import ActionStatus, ActionType, EntryType
from app.repositories.incident_repository import IncidentRepository
from app.repositories.response_action_repository import ResponseActionRepository
from app.services.integrity.hash_chain_ledger import HashChainLedger


class ActionExpiryService:
    """Finds and rolls back actions whose TTL has expired."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._action_repo = ResponseActionRepository(session)
        self._incident_repo = IncidentRepository(session)
        self._ledger = HashChainLedger(session)
        self._fw_connector = SimulatedFirewallConnector(session)
        self._identity_connector = SimulatedIdentityConnector(session)

    async def process_expired_actions(self) -> int:
        """Scan and expire active actions with lapsed TTL."""
        expired = await self._action_repo.list_expired_actions()
        now = datetime.now(timezone.utc)
        count = 0

        for action in expired:
            connector = (
                self._fw_connector
                if action.action_type == ActionType.BLOCK_IP
                else self._identity_connector
            )
            await connector.rollback(action.id, action.target, action.parameters)
            await self._action_repo.update_status(
                action_id=action.id,
                status=ActionStatus.EXPIRED,
                rolled_back_at=now,
                rollback_reason="Automatic TTL expiry",
            )
            await self._incident_repo.add_timeline_entry(
                incident_id=action.incident_id,
                entry_type="ACTION_EXPIRED",
                title=f"Action Expired: {action.action_type.value} on {action.target}",
                description=f"Action automatically expired after {action.ttl_seconds}s TTL.",
                actor="action_expiry_worker",
                metadata={"action_id": str(action.id)},
            )
            await self._ledger.append_entry(
                entry_type=EntryType.ACTION_EXPIRED,
                incident_id=action.incident_id,
                payload={"action_id": str(action.id), "target": action.target},
            )
            count += 1

        return count
