"""Incident lifecycle management service for manual transitions, notes, and resolution."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.enums import EntryType, IncidentStatus, UserRole
from app.domain.exceptions import EntityNotFoundError
from app.domain.incident import Incident, TimelineEntry
from app.domain.incident_state_machine import validate_state_transition
from app.repositories.incident_repository import IncidentRepository
from app.services.integrity.hash_chain_ledger import HashChainLedger


class IncidentLifecycleService:
    """Manages manual analyst transitions, notes, and assignments on incidents."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = IncidentRepository(session)
        self._ledger = HashChainLedger(session)

    async def transition_incident(
        self,
        incident_id: UUID,
        target_status: IncidentStatus,
        user_role: UserRole,
        actor_username: str,
        notes: str | None = None,
    ) -> Incident:
        """Perform a validated manual state transition."""
        incident = await self._repo.get_by_id(incident_id)
        if not incident:
            raise EntityNotFoundError("Incident", str(incident_id))

        validate_state_transition(
            current_status=incident.status,
            target_status=target_status,
            user_role=user_role,
            is_automated=False,
            notes=notes,
        )

        now = datetime.now(UTC)
        closed_at = (
            now
            if target_status
            in (IncidentStatus.RESOLVED, IncidentStatus.CLOSED, IncidentStatus.FALSE_POSITIVE)
            else None
        )

        updated = await self._repo.update_incident(
            incident_id=incident_id,
            status=target_status,
            closed_at=closed_at,
            close_notes=notes if closed_at else incident.close_notes,
        )

        # Add timeline record
        await self._repo.add_timeline_entry(
            incident_id=incident_id,
            entry_type="STATE_TRANSITION",
            title=f"Status changed to {target_status.value}",
            description=f"Transitioned from {incident.status.value} to {target_status.value}. Notes: {notes or 'None'}",
            actor=f"user:{actor_username}",
            metadata={
                "old_status": incident.status.value,
                "new_status": target_status.value,
                "notes": notes,
            },
        )

        # Append to audit ledger
        await self._ledger.append_entry(
            entry_type=EntryType.STATE_TRANSITION,
            incident_id=incident_id,
            payload={
                "old_status": incident.status.value,
                "new_status": target_status.value,
                "actor": actor_username,
                "notes": notes,
            },
        )

        assert updated is not None
        return updated

    async def add_analyst_note(
        self,
        incident_id: UUID,
        note: str,
        actor_username: str,
    ) -> TimelineEntry:
        """Add an analyst investigation note to the incident timeline."""
        incident = await self._repo.get_by_id(incident_id)
        if not incident:
            raise EntityNotFoundError("Incident", str(incident_id))

        timeline_entry = await self._repo.add_timeline_entry(
            incident_id=incident_id,
            entry_type="ANALYST_NOTE",
            title=f"Note by {actor_username}",
            description=note,
            actor=f"user:{actor_username}",
            metadata={"note": note},
        )

        await self._ledger.append_entry(
            entry_type=EntryType.NOTE_ADDED,
            incident_id=incident_id,
            payload={"author": actor_username, "note": note},
        )

        return timeline_entry
