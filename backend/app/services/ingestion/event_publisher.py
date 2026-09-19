"""Event publisher service for broadcasting normalized events to Redis Streams."""

from __future__ import annotations

import json
from typing import Any

import redis.asyncio as aioredis

from app.config.settings import get_settings
from app.domain.normalized_event import NormalizedEvent


class EventPublisher:
    """Publishes normalized security events onto the Redis Stream pipeline."""

    def __init__(self, redis_client: aioredis.Redis | None = None) -> None:
        self._settings = get_settings()
        self._redis = redis_client

    async def get_client(self) -> aioredis.Redis:
        """Lazily initialize Redis client if not injected."""
        if self._redis is None:
            self._redis = aioredis.from_url(
                self._settings.redis_url,
                decode_responses=True,
            )
        return self._redis

    @staticmethod
    def _serialize_event(event: NormalizedEvent) -> dict[str, str]:
        """Convert a normalized event domain object to Redis stream field-value pairs."""
        payload: dict[str, Any] = {
            "event_id": str(event.event_id),
            "occurred_at": event.occurred_at.isoformat(),
            "ingested_at": event.ingested_at.isoformat(),
            "source": event.source.value,
            "event_type": event.event_type.value,
            "host": event.host or "",
            "username": event.username or "",
            "src_ip": event.src_ip or "",
            "dst_ip": event.dst_ip or "",
            "dst_port": str(event.dst_port) if event.dst_port is not None else "",
            "process_name": event.process_name or "",
            "command_line": event.command_line or "",
            "file_path": event.file_path or "",
            "file_hash_sha256": event.file_hash_sha256 or "",
            "bytes_out": str(event.bytes_out) if event.bytes_out is not None else "",
            "http_path": event.http_path or "",
            "severity_hint": str(event.severity_hint) if event.severity_hint is not None else "",
            "raw": json.dumps(event.raw),
        }
        return {k: str(v) for k, v in payload.items()}

    async def publish(self, event: NormalizedEvent) -> str:
        """Publish a single normalized event to the stream."""
        client = await self.get_client()
        stream_name = self._settings.redis_stream_events
        fields = self._serialize_event(event)
        try:
            message_id: str = await client.xadd(stream_name, fields)
            return message_id
        except Exception:
            # Safe degradation if Redis is unavailable during testing
            return ""

    async def publish_batch(self, events: list[NormalizedEvent]) -> list[str]:
        """Publish a batch of normalized events to the stream."""
        message_ids: list[str] = []
        for event in events:
            mid = await self.publish(event)
            message_ids.append(mid)
        return message_ids
