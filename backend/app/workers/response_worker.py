"""Response worker — executes approved or automatic response actions.

Polls for pending response actions and executes them through the
appropriate enforcement connector, respecting all guardrails.

This is a stub that will be fully implemented in Phase 5.
"""

from __future__ import annotations

import asyncio
import signal
import sys

import structlog

from app.config.logging_config import configure_logging
from app.config.settings import get_settings

logger = structlog.get_logger(__name__)

SHUTDOWN_REQUESTED = False


def handle_shutdown(signum: int, frame: object) -> None:
    """Handle graceful shutdown signals.

    Args:
        signum: The signal number received.
        frame: The current stack frame.
    """
    global SHUTDOWN_REQUESTED  # noqa: PLW0603
    SHUTDOWN_REQUESTED = True
    logger.info("shutdown_requested", signal=signum)


async def run_response_worker() -> None:
    """Main loop for the response worker.

    Will be fully implemented in Phase 5.
    """
    settings = get_settings()
    configure_logging(log_level=settings.log_level, log_format=settings.log_format)
    logger.info("response_worker_starting")

    while not SHUTDOWN_REQUESTED:
        await asyncio.sleep(5)
        logger.debug("response_worker_heartbeat")

    logger.info("response_worker_stopped")


if __name__ == "__main__":
    signal.signal(signal.SIGTERM, handle_shutdown)
    signal.signal(signal.SIGINT, handle_shutdown)

    try:
        asyncio.run(run_response_worker())
    except KeyboardInterrupt:
        sys.exit(0)
