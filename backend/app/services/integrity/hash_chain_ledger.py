"""Cryptographic hash chain ledger service."""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.orm_models import AuditLedgerEntryOrm
from app.domain.enums import EntryType
from app.repositories.audit_ledger_repository import AuditLedgerEntry, AuditLedgerRepository
from app.services.integrity.canonical_json import canonical_bytes

GENESIS_PREVIOUS_HASH = "0" * 64


def compute_entry_hash(
    sequence_number: int,
    entry_type: EntryType,
    incident_id: UUID | None,
    payload: dict[str, Any],
    created_at: datetime,
    previous_hash: str,
) -> str:
    """Compute the deterministic SHA-256 hash for a ledger entry.

    Formula:
        SHA256( canonical_json(entry_type, incident_id, payload, created_at, sequence_number) || previous_hash )
    """
    canonical_dict = {
        "sequence_number": sequence_number,
        "entry_type": entry_type.value if hasattr(entry_type, "value") else str(entry_type),
        "incident_id": str(incident_id) if incident_id else None,
        "payload": payload,
        "created_at": created_at,
    }
    content_bytes = canonical_bytes(canonical_dict)
    combined = content_bytes + previous_hash.encode("utf-8")
    return hashlib.sha256(combined).hexdigest()


class HashChainLedger:
    """Manages append-only cryptographic hash chaining in the PostgreSQL audit ledger."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = AuditLedgerRepository(session)

    async def append_entry(
        self,
        entry_type: EntryType,
        payload: dict[str, Any],
        incident_id: UUID | None = None,
    ) -> AuditLedgerEntry:
        """Append a new tamper-evident record to the audit ledger.

        Executes within the existing transaction, acquiring the next sequence number
        and chaining onto the latest hash.
        """
        now = datetime.now(UTC)

        # Get latest entry to obtain previous hash and next sequence number
        latest = await self._repo.get_latest_entry()
        if latest is None:
            previous_hash = GENESIS_PREVIOUS_HASH
            next_seq = 1
        else:
            previous_hash = latest.entry_hash
            next_seq = latest.sequence_number + 1

        entry_hash = compute_entry_hash(
            sequence_number=next_seq,
            entry_type=entry_type,
            incident_id=incident_id,
            payload=payload,
            created_at=now,
            previous_hash=previous_hash,
        )

        orm = AuditLedgerEntryOrm(
            sequence_number=next_seq,
            entry_type=entry_type,
            incident_id=incident_id,
            payload=payload,
            created_at=now,
            previous_hash=previous_hash,
            entry_hash=entry_hash,
        )
        self._session.add(orm)
        await self._session.flush()
        return self._repo._to_domain(orm)
