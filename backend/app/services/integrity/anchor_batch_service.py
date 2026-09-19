"""Anchor batching service coordinating Merkle tree construction and on-chain submission."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.blockchain.anchor_chain_client import AnchorChainClient
from app.domain.enums import AnchorStatus
from app.domain.exceptions import BlockchainClientError
from app.repositories.anchor_batch_repository import AnchorBatch, AnchorBatchRepository
from app.repositories.audit_ledger_repository import AuditLedgerRepository
from app.services.integrity.merkle_tree import MerkleTree


class AnchorBatchService:
    """Collects unanchored audit ledger entries, builds Merkle trees, and anchors them to blockchain."""

    def __init__(
        self,
        session: AsyncSession,
        chain_client: AnchorChainClient | None = None,
    ) -> None:
        self._session = session
        self._ledger_repo = AuditLedgerRepository(session)
        self._batch_repo = AnchorBatchRepository(session)
        self._chain_client = chain_client or AnchorChainClient()

    async def create_and_anchor_batch(self, max_entries: int = 500) -> AnchorBatch | None:
        """Create a new batch from unanchored entries and anchor it to the smart contract."""
        entries = await self._ledger_repo.list_unanchored_entries(limit=max_entries)
        if not entries:
            return None

        from_seq = entries[0].sequence_number
        to_seq = entries[-1].sequence_number
        entry_hashes = [e.entry_hash for e in entries]

        # Construct Merkle tree
        tree = MerkleTree(entry_hashes)
        merkle_root = tree.root

        # Create pending batch
        batch = await self._batch_repo.create(
            from_sequence=from_seq,
            to_sequence=to_seq,
            merkle_root=merkle_root,
            entry_count=len(entries),
            status=AnchorStatus.PENDING,
        )

        # Mark ledger entries as attached to this batch
        await self._ledger_repo.mark_anchored(from_seq, to_seq, batch.id)

        # Submit on-chain
        try:
            receipt = await self._chain_client.anchor_root(
                merkle_root=merkle_root,
                from_sequence=from_seq,
                to_sequence=to_seq,
            )
            confirmed_batch = await self._batch_repo.update_confirmed(
                batch_id=batch.id,
                tx_hash=receipt.tx_hash,
                block_number=receipt.block_number,
                contract_address=receipt.contract_address,
            )
            return confirmed_batch
        except BlockchainClientError as err:
            await self._batch_repo.update_failed(batch.id, str(err))
            # Safe degradation: do not throw to caller
            return batch
