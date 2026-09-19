"""Integrity and cryptographic ledger schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID
from pydantic import BaseModel, Field

from app.domain.enums import AnchorStatus, EntryType, VerificationStatus


class AuditLedgerEntryResponse(BaseModel):
    """Ledger entry representation."""

    sequence_number: int
    entry_type: EntryType
    incident_id: UUID | None
    payload: dict[str, Any]
    created_at: datetime
    previous_hash: str
    entry_hash: str
    anchor_batch_id: UUID | None = None


class AnchorBatchResponse(BaseModel):
    """On-chain Merkle root anchor batch representation."""

    id: UUID
    from_sequence: int
    to_sequence: int
    merkle_root: str
    entry_count: int
    status: AnchorStatus
    tx_hash: str | None
    block_number: int | None
    contract_address: str | None
    error_message: str | None
    created_at: datetime
    anchored_at: datetime | None


class MerkleProofStepSchema(BaseModel):
    """Single step in Merkle tree path."""

    position: str
    hash_value: str


class MerkleProofResponse(BaseModel):
    """Merkle inclusion proof for an individual ledger entry."""

    leaf_hash: str
    leaf_index: int
    total_leaves: int
    proof_steps: list[MerkleProofStepSchema]
    root: str


class IntegrityVerificationResponse(BaseModel):
    """Complete cryptographic integrity verification report."""

    status: VerificationStatus
    total_entries_checked: int
    total_batches_checked: int
    tampered_sequence_number: int | None = None
    tampered_batch_id: UUID | None = None
    explanation: str
    chain_head_hash: str | None = None
    verified_at: datetime = Field(default_factory=datetime.utcnow)
