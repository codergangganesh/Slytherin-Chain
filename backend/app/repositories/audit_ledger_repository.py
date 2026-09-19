"""Repository for Audit Ledger hash-chain data access."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.orm_models import AuditLedgerEntryOrm
from app.domain.enums import EntryType


@dataclass(frozen=True)
class AuditLedgerEntry:
    """Represents an immutable ledger record."""

    sequence_number: int
    entry_type: EntryType
    incident_id: UUID | None
    payload: dict[str, Any]
    created_at: datetime
    previous_hash: str
    entry_hash: str
    anchor_batch_id: UUID | None = None


class AuditLedgerRepository:
    """Encapsulates database operations for the hash-chain audit ledger."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @staticmethod
    def _to_domain(orm: AuditLedgerEntryOrm) -> AuditLedgerEntry:
        """Convert ORM model to domain AuditLedgerEntry."""
        return AuditLedgerEntry(
            sequence_number=orm.sequence_number,
            entry_type=EntryType(orm.entry_type),
            incident_id=orm.incident_id,
            payload=orm.payload or {},
            created_at=orm.created_at,
            previous_hash=orm.previous_hash,
            entry_hash=orm.entry_hash,
            anchor_batch_id=orm.anchor_batch_id,
        )

    async def get_latest_entry(self) -> AuditLedgerEntry | None:
        """Get the most recent ledger entry."""
        stmt = (
            select(AuditLedgerEntryOrm)
            .order_by(AuditLedgerEntryOrm.sequence_number.desc())
            .limit(1)
        )
        result = await self._session.execute(stmt)
        orm = result.scalar_one_or_none()
        return self._to_domain(orm) if orm else None

    async def get_by_sequence(self, sequence_number: int) -> AuditLedgerEntry | None:
        """Get ledger entry by sequence number."""
        stmt = select(AuditLedgerEntryOrm).where(
            AuditLedgerEntryOrm.sequence_number == sequence_number
        )
        result = await self._session.execute(stmt)
        orm = result.scalar_one_or_none()
        return self._to_domain(orm) if orm else None

    async def list_entries(
        self,
        incident_id: UUID | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[AuditLedgerEntry], int]:
        """List ledger entries with optional incident filter."""
        stmt = select(AuditLedgerEntryOrm)
        count_stmt = select(func.count()).select_from(AuditLedgerEntryOrm)

        if incident_id:
            stmt = stmt.where(AuditLedgerEntryOrm.incident_id == incident_id)
            count_stmt = count_stmt.where(AuditLedgerEntryOrm.incident_id == incident_id)

        total = await self._session.scalar(count_stmt) or 0
        result = await self._session.execute(
            stmt.order_by(AuditLedgerEntryOrm.sequence_number.asc()).limit(limit).offset(offset)
        )
        return [self._to_domain(orm) for orm in result.scalars().all()], total

    async def list_unanchored_entries(self, limit: int = 500) -> list[AuditLedgerEntry]:
        """Fetch unanchored ledger entries in sequence order."""
        stmt = (
            select(AuditLedgerEntryOrm)
            .where(AuditLedgerEntryOrm.anchor_batch_id.is_(None))
            .order_by(AuditLedgerEntryOrm.sequence_number.asc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return [self._to_domain(orm) for orm in result.scalars().all()]

    async def mark_anchored(self, from_seq: int, to_seq: int, batch_id: UUID) -> None:
        """Assign anchor batch ID to a range of entries."""
        from sqlalchemy import update

        stmt = (
            update(AuditLedgerEntryOrm)
            .where(
                AuditLedgerEntryOrm.sequence_number >= from_seq,
                AuditLedgerEntryOrm.sequence_number <= to_seq,
            )
            .values(anchor_batch_id=batch_id)
        )
        await self._session.execute(stmt)
        await self._session.flush()
