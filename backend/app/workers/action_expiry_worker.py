"""Background worker continuously checking and expiring lapsed TTL actions."""

from __future__ import annotations

import asyncio
import logging

from app.db.session import get_session_factory
from app.services.response.action_expiry_service import ActionExpiryService

logger = logging.getLogger("sentinelchain.action_expiry_worker")


class ActionExpiryWorker:
    """Periodically scans database for expired actions and applies rollbacks."""

    def __init__(self, check_interval_seconds: int = 15) -> None:
        self._interval = check_interval_seconds
        self._running = False

    async def run(self) -> None:
        """Periodic scan loop."""
        self._running = True
        session_factory = get_session_factory()
        logger.info(f"Action expiry worker started (scan interval: {self._interval}s)")

        while self._running:
            try:
                async with session_factory() as session:
                    service = ActionExpiryService(session)
                    count = await service.process_expired_actions()
                    if count > 0:
                        logger.info(f"Expired and rolled back {count} response actions")
                    await session.commit()
            except asyncio.CancelledError:
                break
            except Exception as err:
                logger.error(f"Error in action expiry scan: {err}")

            await asyncio.sleep(self._interval)

    def stop(self) -> None:
        self._running = False


if __name__ == "__main__":
    worker = ActionExpiryWorker()
    try:
        asyncio.run(worker.run())
    except KeyboardInterrupt:
        worker.stop()

