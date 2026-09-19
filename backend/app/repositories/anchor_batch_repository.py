"""Repository for on-chain anchor batches."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.orm_models import AnchorBatchOrm
from app.domain.enums import AnchorStatus


@dataclass(frozen=True)
class AnchorBatch:
    """Represents an on-chain batch of anchored Merkle roots."""

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


class AnchorBatchRepository:
    """Encapsulates database access for anchor batches."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @staticmethod
    def _to_domain(orm: AnchorBatchOrm) -> AnchorBatch:
        return AnchorBatch(
            id=orm.id,
            from_sequence=orm.from_sequence,
            to_sequence=orm.to_sequence,
            merkle_root=orm.merkle_root,
            entry_count=orm.entry_count,
            status=AnchorStatus(orm.status),
            tx_hash=orm.tx_hash,
            block_number=orm.block_number,
            contract_address=orm.contract_address,
            error_message=orm.error_message,
            created_at=orm.created_at,
            anchored_at=orm.anchored_at,
        )

    async def create(
        self,
        from_sequence: int,
        to_sequence: int,
        merkle_root: str,
        entry_count: int,
        status: AnchorStatus = AnchorStatus.PENDING,
    ) -> AnchorBatch:
        """Create a new pending anchor batch."""
        orm = AnchorBatchOrm(
            from_sequence=from_sequence,
            to_sequence=to_sequence,
            merkle_root=merkle_root,
            entry_count=entry_count,
            status=status,
        )
        self._session.add(orm)
        await self._session.flush()
        await self._session.refresh(orm)
        return self._to_domain(orm)

    async def update_confirmed(
        self,
        batch_id: UUID,
        tx_hash: str,
        block_number: int,
        contract_address: str,
    ) -> AnchorBatch | None:
        """Mark batch confirmed with transaction hash."""
        stmt = select(AnchorBatchOrm).where(AnchorBatchOrm.id == batch_id)
        result = await self._session.execute(stmt)
        orm = result.scalar_one_or_none()
        if not orm:
            return None

        orm.status = AnchorStatus.CONFIRMED
        orm.tx_hash = tx_hash
        orm.block_number = block_number
        orm.contract_address = contract_address
        orm.anchored_at = datetime.now(UTC)
        await self._session.flush()
        await self._session.refresh(orm)
        return self._to_domain(orm)

    async def update_failed(self, batch_id: UUID, error_message: str) -> None:
        """Mark batch failed."""
        stmt = select(AnchorBatchOrm).where(AnchorBatchOrm.id == batch_id)
        result = await self._session.execute(stmt)
        orm = result.scalar_one_or_none()
        if orm:
            orm.status = AnchorStatus.FAILED
            orm.error_message = error_message
            await self._session.flush()

    async def get_by_id(self, batch_id: UUID) -> AnchorBatch | None:
        """Find batch by ID."""
        stmt = select(AnchorBatchOrm).where(AnchorBatchOrm.id == batch_id)
        result = await self._session.execute(stmt)
        orm = result.scalar_one_or_none()
        return self._to_domain(orm) if orm else None

    async def list_batches(self, limit: int = 50, offset: int = 0) -> tuple[list[AnchorBatch], int]:
        """List anchor batches descending."""
        stmt = select(AnchorBatchOrm)
        count_stmt = select(func.count()).select_from(AnchorBatchOrm)

        total = await self._session.scalar(count_stmt) or 0
        result = await self._session.execute(
            stmt.order_by(AnchorBatchOrm.created_at.desc()).limit(limit).offset(offset)
        )
        return [self._to_domain(orm) for orm in result.scalars().all()], total
