"""Background worker periodically anchoring batches of audit ledger records onto the blockchain."""

from __future__ import annotations

import asyncio
import logging

from app.config.settings import get_settings
from app.db.session import get_session_factory
from app.services.integrity.anchor_batch_service import AnchorBatchService

logger = logging.getLogger("sentinelchain.anchor_worker")


class AnchorWorker:
    """Periodically triggers Merkle batch construction and Web3 on-chain anchoring."""

    def __init__(self) -> None:
        self._settings = get_settings()
        self._interval = self._settings.anchor_interval_seconds
        self._running = False

    async def run(self) -> None:
        """Periodic anchoring execution loop."""
        self._running = True
        session_factory = get_session_factory()
        logger.info(f"Anchor worker started (Interval: {self._interval}s)")

        while self._running:
            try:
                async with session_factory() as session:
                    batch_service = AnchorBatchService(session)
                    batch = await batch_service.create_and_anchor_batch()
                    if batch:
                        logger.info(
                            f"Anchored batch {batch.id} (seq {batch.from_sequence}..{batch.to_sequence}, "
                            f"status: {batch.status.value}, tx: {batch.tx_hash})"
                        )
                    await session.commit()
            except asyncio.CancelledError:
                break
            except Exception as err:
                logger.error(f"Error in anchor worker execution: {err}")

            await asyncio.sleep(self._interval)

    def stop(self) -> None:
        self._running = False


if __name__ == "__main__":
    worker = AnchorWorker()
    try:
        asyncio.run(worker.run())
    except KeyboardInterrupt:
        worker.stop()
