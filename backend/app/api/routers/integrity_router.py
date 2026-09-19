"""API router for Integrity verification, Hash chain ledger, and On-chain batches."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import require_analyst, require_viewer
from app.api.schemas.common_schemas import PaginatedResponse
from app.api.schemas.integrity_schemas import (
    AnchorBatchResponse,
    AuditLedgerEntryResponse,
    IntegrityVerificationResponse,
    MerkleProofResponse,
    MerkleProofStepSchema,
)
from app.db.session import get_db_session
from app.domain.user import User
from app.repositories.anchor_batch_repository import AnchorBatchRepository
from app.repositories.audit_ledger_repository import AuditLedgerRepository
from app.services.integrity.anchor_batch_service import AnchorBatchService
from app.services.integrity.integrity_verification_service import (
    IntegrityVerificationService,
)

router = APIRouter(prefix="/integrity", tags=["Integrity & Blockchain"])


@router.get("/status", response_model=IntegrityVerificationResponse)
async def get_integrity_status(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[User, Depends(require_viewer)],
) -> IntegrityVerificationResponse:
    """Check current cryptographic verification status across ledger and on-chain batches."""
    verification_service = IntegrityVerificationService(session)
    res = await verification_service.verify_ledger()
    return IntegrityVerificationResponse(
        status=res.status,
        total_entries_checked=res.total_entries_checked,
        total_batches_checked=res.total_batches_checked,
        tampered_sequence_number=res.tampered_sequence_number,
        tampered_batch_id=res.tampered_batch_id,
        explanation=res.explanation,
        chain_head_hash=res.chain_head_hash,
    )


@router.post("/verify", response_model=IntegrityVerificationResponse)
async def trigger_deep_verification(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[User, Depends(require_viewer)],
) -> IntegrityVerificationResponse:
    """Trigger an explicit on-demand deep cryptographic verification."""
    verification_service = IntegrityVerificationService(session)
    res = await verification_service.verify_ledger()
    return IntegrityVerificationResponse(
        status=res.status,
        total_entries_checked=res.total_entries_checked,
        total_batches_checked=res.total_batches_checked,
        tampered_sequence_number=res.tampered_sequence_number,
        tampered_batch_id=res.tampered_batch_id,
        explanation=res.explanation,
        chain_head_hash=res.chain_head_hash,
    )


@router.get("/entries", response_model=PaginatedResponse[AuditLedgerEntryResponse])
@router.get(
    "/ledger", response_model=PaginatedResponse[AuditLedgerEntryResponse], include_in_schema=False
)
async def list_ledger_entries(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[User, Depends(require_viewer)],
    incident_id: UUID | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> PaginatedResponse[AuditLedgerEntryResponse]:
    """Retrieve audit ledger hash-chain entries with pagination."""
    repo = AuditLedgerRepository(session)
    entries, total = await repo.list_entries(incident_id=incident_id, limit=limit, offset=offset)
    items = [
        AuditLedgerEntryResponse(
            sequence_number=e.sequence_number,
            entry_type=e.entry_type,
            incident_id=e.incident_id,
            payload=e.payload,
            created_at=e.created_at,
            previous_hash=e.previous_hash,
            entry_hash=e.entry_hash,
            anchor_batch_id=e.anchor_batch_id,
        )
        for e in entries
    ]
    return PaginatedResponse(items=items, total=total, limit=limit, offset=offset)


@router.get("/entries/{sequence_number}/proof", response_model=MerkleProofResponse)
async def get_entry_merkle_proof(
    sequence_number: int,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[User, Depends(require_viewer)],
) -> MerkleProofResponse:
    """Generate a Merkle inclusion proof for a specific anchored entry."""
    verification_service = IntegrityVerificationService(session)
    proof = await verification_service.get_entry_merkle_proof(sequence_number)
    if not proof:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "PROOF_NOT_AVAILABLE",
                    "message": f"Entry #{sequence_number} not anchored yet",
                }
            },
        )

    return MerkleProofResponse(
        leaf_hash=proof.leaf_hash,
        leaf_index=proof.leaf_index,
        total_leaves=proof.total_leaves,
        proof_steps=[
            MerkleProofStepSchema(position=s.position, hash_value=s.hash_value)
            for s in proof.proof_steps
        ],
        root=proof.root,
    )


@router.get("/batches", response_model=PaginatedResponse[AnchorBatchResponse])
async def list_anchor_batches(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[User, Depends(require_viewer)],
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> PaginatedResponse[AnchorBatchResponse]:
    """List on-chain Merkle root anchor batches."""
    repo = AnchorBatchRepository(session)
    batches, total = await repo.list_batches(limit=limit, offset=offset)
    items = [
        AnchorBatchResponse(
            id=b.id,
            from_sequence=b.from_sequence,
            to_sequence=b.to_sequence,
            merkle_root=b.merkle_root,
            entry_count=b.entry_count,
            status=b.status,
            tx_hash=b.tx_hash,
            block_number=b.block_number,
            contract_address=b.contract_address,
            error_message=b.error_message,
            created_at=b.created_at,
            anchored_at=b.anchored_at,
        )
        for b in batches
    ]
    return PaginatedResponse(items=items, total=total, limit=limit, offset=offset)


@router.post("/anchor-now", response_model=AnchorBatchResponse)
async def trigger_manual_anchor(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[User, Depends(require_analyst)],
) -> AnchorBatchResponse:
    """Manually trigger immediate batching and on-chain anchoring (Analyst role)."""
    batch_service = AnchorBatchService(session)
    batch = await batch_service.create_and_anchor_batch()
    if not batch:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": "NO_UNANCHORED_ENTRIES",
                    "message": "No unanchored ledger entries available",
                }
            },
        )

    return AnchorBatchResponse(
        id=batch.id,
        from_sequence=batch.from_sequence,
        to_sequence=batch.to_sequence,
        merkle_root=batch.merkle_root,
        entry_count=batch.entry_count,
        status=batch.status,
        tx_hash=batch.tx_hash,
        block_number=batch.block_number,
        contract_address=batch.contract_address,
        error_message=batch.error_message,
        created_at=batch.created_at,
        anchored_at=batch.anchored_at,
    )
