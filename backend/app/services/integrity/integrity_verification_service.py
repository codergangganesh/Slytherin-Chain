"""Integrity verification service executing 3-tier validation (Chain, Batch, On-Chain)."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.orm_models import AnchorBatchOrm, AuditLedgerEntryOrm
from app.domain.enums import VerificationStatus
from app.repositories.anchor_batch_repository import AnchorBatchRepository
from app.repositories.audit_ledger_repository import AuditLedgerRepository
from app.services.integrity.hash_chain_ledger import (
    GENESIS_PREVIOUS_HASH,
    compute_entry_hash,
)
from app.services.integrity.merkle_tree import MerkleProof, MerkleTree


@dataclass(frozen=True)
class VerificationResult:
    """Detailed verdict of integrity verification."""

    status: VerificationStatus
    total_entries_checked: int
    total_batches_checked: int
    tampered_sequence_number: int | None
    tampered_batch_id: UUID | None
    explanation: str
    chain_head_hash: str | None


class IntegrityVerificationService:
    """Performs deep cryptographic auditing of the hash chain and Merkle batches."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._ledger_repo = AuditLedgerRepository(session)
        self._batch_repo = AnchorBatchRepository(session)

    async def verify_ledger(self) -> VerificationResult:
        """Perform end-to-end cryptographic verification of the complete ledger."""
        # Fetch all ledger entries in sequence order
        stmt = select(AuditLedgerEntryOrm).order_by(AuditLedgerEntryOrm.sequence_number.asc())
        res = await self._session.execute(stmt)
        entries = res.scalars().all()

        if not entries:
            return VerificationResult(
                status=VerificationStatus.VERIFIED,
                total_entries_checked=0,
                total_batches_checked=0,
                tampered_sequence_number=None,
                tampered_batch_id=None,
                explanation="Ledger is empty (Genesis state).",
                chain_head_hash=GENESIS_PREVIOUS_HASH,
            )

        # ── TIER 1: Hash Chain Verification ───────────────────────────────────
        expected_prev = GENESIS_PREVIOUS_HASH
        for entry in entries:
            # Check previous hash link
            if entry.previous_hash != expected_prev:
                return VerificationResult(
                    status=VerificationStatus.TAMPERED,
                    total_entries_checked=len(entries),
                    total_batches_checked=0,
                    tampered_sequence_number=entry.sequence_number,
                    tampered_batch_id=entry.anchor_batch_id,
                    explanation=(
                        f"Hash chain link broken at sequence #{entry.sequence_number}. "
                        f"Expected previous hash {expected_prev[:16]}..., found {entry.previous_hash[:16]}..."
                    ),
                    chain_head_hash=entries[-1].entry_hash,
                )

            # Recompute entry hash from raw stored payload
            recomputed = compute_entry_hash(
                sequence_number=entry.sequence_number,
                entry_type=entry.entry_type,
                incident_id=entry.incident_id,
                payload=entry.payload,
                created_at=entry.created_at,
                previous_hash=entry.previous_hash,
            )

            if recomputed != entry.entry_hash:
                return VerificationResult(
                    status=VerificationStatus.TAMPERED,
                    total_entries_checked=len(entries),
                    total_batches_checked=0,
                    tampered_sequence_number=entry.sequence_number,
                    tampered_batch_id=entry.anchor_batch_id,
                    explanation=(
                        f"Payload tampering detected at sequence #{entry.sequence_number}! "
                        f"Stored hash does not match canonical recomputed hash."
                    ),
                    chain_head_hash=entries[-1].entry_hash,
                )

            expected_prev = entry.entry_hash

        # ── TIER 2: Merkle Batch Verification ─────────────────────────────────
        stmt_batches = select(AnchorBatchOrm).order_by(AnchorBatchOrm.from_sequence.asc())
        res_batches = await self._session.execute(stmt_batches)
        batches = res_batches.scalars().all()

        for batch in batches:
            batch_entries = [
                e for e in entries if batch.from_sequence <= e.sequence_number <= batch.to_sequence
            ]
            if not batch_entries:
                continue

            entry_hashes = [e.entry_hash for e in batch_entries]
            tree = MerkleTree(entry_hashes)
            if tree.root.lower() != batch.merkle_root.lower():
                return VerificationResult(
                    status=VerificationStatus.TAMPERED,
                    total_entries_checked=len(entries),
                    total_batches_checked=len(batches),
                    tampered_sequence_number=batch.from_sequence,
                    tampered_batch_id=batch.id,
                    explanation=(
                        f"Merkle root mismatch for batch {batch.id}. "
                        f"Recomputed {tree.root} != stored {batch.merkle_root}"
                    ),
                    chain_head_hash=entries[-1].entry_hash,
                )

        # Check for unanchored entries
        unanchored = [e for e in entries if e.anchor_batch_id is None]
        if unanchored:
            return VerificationResult(
                status=VerificationStatus.PENDING_ANCHOR,
                total_entries_checked=len(entries),
                total_batches_checked=len(batches),
                tampered_sequence_number=None,
                tampered_batch_id=None,
                explanation=f"All {len(entries)} entries verified. {len(unanchored)} recent entries pending on-chain anchor.",
                chain_head_hash=entries[-1].entry_hash,
            )

        return VerificationResult(
            status=VerificationStatus.VERIFIED,
            total_entries_checked=len(entries),
            total_batches_checked=len(batches),
            tampered_sequence_number=None,
            tampered_batch_id=None,
            explanation=f"Complete integrity verified! {len(entries)} entries across {len(batches)} batches cryptographically intact.",
            chain_head_hash=entries[-1].entry_hash,
        )

    async def get_entry_merkle_proof(self, sequence_number: int) -> MerkleProof | None:
        """Generate a Merkle inclusion proof for a single entry."""
        entry = await self._ledger_repo.get_by_sequence(sequence_number)
        if not entry or not entry.anchor_batch_id:
            return None

        batch = await self._batch_repo.get_by_id(entry.anchor_batch_id)
        if not batch:
            return None

        stmt = (
            select(AuditLedgerEntryOrm)
            .where(
                AuditLedgerEntryOrm.sequence_number >= batch.from_sequence,
                AuditLedgerEntryOrm.sequence_number <= batch.to_sequence,
            )
            .order_by(AuditLedgerEntryOrm.sequence_number.asc())
        )
        res = await self._session.execute(stmt)
        batch_entries = res.scalars().all()

        entry_hashes = [e.entry_hash for e in batch_entries]
        tree = MerkleTree(entry_hashes)

        leaf_idx = sequence_number - batch.from_sequence
        return tree.get_proof(leaf_idx)
