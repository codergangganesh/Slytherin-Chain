"""Background worker consuming normalized events from Redis Streams and running detection."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any
import uuid

import redis.asyncio as aioredis

from app.config.settings import get_settings
from app.db.session import get_session_factory
from app.domain.enums import EventSource, EventType
from app.domain.normalized_event import NormalizedEvent
from app.services.detection.detection_service import DetectionService
from app.services.enrichment.asset_context_service import AssetContextService
from app.services.enrichment.threat_intel_service import ThreatIntelService
from app.services.incident_correlation_service import IncidentCorrelationService
from app.services.response.response_orchestrator import ResponseOrchestrator

logger = logging.getLogger("sentinelchain.detection_worker")


def parse_stream_event(data: dict[str, str]) -> NormalizedEvent:
    """Reconstruct NormalizedEvent from Redis Stream string dictionary."""
    from datetime import datetime

    raw_data = json.loads(data.get("raw", "{}"))
    return NormalizedEvent(
        event_id=uuid.UUID(data["event_id"]),
        occurred_at=datetime.fromisoformat(data["occurred_at"]),
        ingested_at=datetime.fromisoformat(data["ingested_at"]),
        source=EventSource(data["source"]),
        event_type=EventType(data["event_type"]),
        host=data.get("host") or None,
        username=data.get("username") or None,
        src_ip=data.get("src_ip") or None,
        dst_ip=data.get("dst_ip") or None,
        dst_port=int(data["dst_port"]) if data.get("dst_port") else None,
        process_name=data.get("process_name") or None,
        command_line=data.get("command_line") or None,
        file_path=data.get("file_path") or None,
        file_hash_sha256=data.get("file_hash_sha256") or None,
        bytes_out=int(data["bytes_out"]) if data.get("bytes_out") else None,
        http_path=data.get("http_path") or None,
        severity_hint=int(data["severity_hint"]) if data.get("severity_hint") else None,
        raw=raw_data,
    )


class DetectionWorker:
    """Async background worker consuming events.normalized Redis stream."""

    def __init__(self) -> None:
        self._settings = get_settings()
        self._running = False
        self._detection_service = DetectionService()

    async def run(self) -> None:
        """Main consumer loop."""
        self._running = True
        redis_client = aioredis.from_url(self._settings.redis_url, decode_responses=True)
        stream_name = self._settings.redis_stream_events
        group_name = self._settings.redis_consumer_group
        consumer_name = f"worker-{uuid.uuid4().hex[:8]}"

        # Create consumer group if not exists
        try:
            await redis_client.xgroup_create(stream_name, group_name, id="0", mkstream=True)
        except Exception:
            pass  # Group already exists

        session_factory = get_session_factory()
        logger.info(f"Detection worker '{consumer_name}' started listening on {stream_name}")

        while self._running:
            try:
                # Read new messages from stream
                messages: Any = await redis_client.xreadgroup(
                    group_name,
                    consumer_name,
                    {stream_name: ">"},
                    count=10,
                    block=2000,
                )
                if not messages:
                    continue

                for _, stream_messages in messages:
                    for msg_id, data in stream_messages:
                        try:
                            event = parse_stream_event(data)
                            async with session_factory() as session:
                                alerts = await self._detection_service.process_event(event, session)
                                if alerts:
                                    correlation_service = IncidentCorrelationService(
                                        session=session,
                                        threat_intel_service=ThreatIntelService(session=session),
                                        asset_context_service=AssetContextService(session=session),
                                    )
                                    orchestrator = ResponseOrchestrator(session=session)
                                    for alert in alerts:
                                        incident = await correlation_service.correlate_alert(alert)
                                        # Run autonomous response orchestrator
                                        await orchestrator.evaluate_incident(incident)
                                await session.commit()
                            # Acknowledge stream message
                            await redis_client.xack(stream_name, group_name, msg_id)
                        except Exception as e:
                            logger.error(f"Error processing message {msg_id}: {e}", exc_info=True)
            except asyncio.CancelledError:
                break
            except Exception as err:
                logger.error(f"Detection worker loop error: {err}")
                await asyncio.sleep(1)

        await redis_client.close()

    def stop(self) -> None:
        """Signal the worker to stop running."""
        self._running = False


if __name__ == "__main__":
    worker = DetectionWorker()
    try:
        asyncio.run(worker.run())
    except KeyboardInterrupt:
        worker.stop()
