"""Sliding window counter and state tracking for threshold, distinct count, and sequence rules."""

from __future__ import annotations

from collections import defaultdict
import time
from typing import Any

import redis.asyncio as aioredis

from app.config.settings import get_settings


class SlidingWindowCounter:
    """Maintains time-windowed state across events in Redis with an in-memory fallback."""

    _redis_available: bool = True

    def __init__(self, redis_client: aioredis.Redis | None = None) -> None:
        self._redis = redis_client
        self._settings = get_settings()
        # In-memory fallback: key -> list of (timestamp, value, event_id)
        self._mem_store: dict[str, list[tuple[float, str, str]]] = defaultdict(list)

    async def get_client(self) -> aioredis.Redis | None:
        """Lazily initialize Redis client."""
        if not SlidingWindowCounter._redis_available:
            return None
        if self._redis is None:
            try:
                self._redis = aioredis.from_url(
                    self._settings.redis_url,
                    decode_responses=True,
                    socket_connect_timeout=0.2,
                    socket_timeout=0.2,
                )
            except Exception:
                SlidingWindowCounter._redis_available = False
                self._redis = None
        return self._redis

    async def record_and_count(
        self,
        key: str,
        event_id: str,
        timestamp: float,
        window_seconds: int,
        distinct_val: str | None = None,
    ) -> tuple[int, list[str]]:
        """Record an event occurrence and return the count and event IDs within the window.

        Args:
            key: Grouping key (e.g. "threshold:SSH-001:192.168.1.100").
            event_id: UUID string of the event.
            timestamp: Epoch timestamp of the event.
            window_seconds: Size of the time window in seconds.
            distinct_val: If tracking distinct values (e.g., dst_port), the value string.

        Returns:
            tuple[int, list[str]]: (count or distinct count, list of matched event IDs).
        """
        client = await self.get_client()
        cutoff = timestamp - window_seconds
        member_val = f"{distinct_val}:{event_id}" if distinct_val else f"{event_id}:{event_id}"

        if client is not None:
            try:
                # Add current entry
                await client.zadd(key, {member_val: timestamp})
                # Remove expired entries
                await client.zremrangebyscore(key, "-inf", cutoff)
                await client.expire(key, window_seconds * 2)

                # Fetch all valid entries in window
                entries = await client.zrangebyscore(key, cutoff, "+inf")
                matched_ids: list[str] = []
                distinct_set: set[str] = set()

                for entry in entries:
                    parts = entry.split(":", 1)
                    val = parts[0]
                    eid = parts[1] if len(parts) > 1 else parts[0]
                    distinct_set.add(val)
                    matched_ids.append(eid)

                count = len(distinct_set) if distinct_val else len(matched_ids)
                return count, matched_ids
            except Exception:
                # Fallback to memory on Redis error
                SlidingWindowCounter._redis_available = False

        # Memory Fallback
        store = self._mem_store[key]
        store.append((timestamp, distinct_val or event_id, event_id))
        # Filter window
        store = [item for item in store if item[0] >= cutoff]
        self._mem_store[key] = store

        matched_ids = [item[2] for item in store]
        if distinct_val:
            distinct_set = {item[1] for item in store}
            return len(distinct_set), matched_ids
        return len(store), matched_ids

    async def record_sequence_step(
        self,
        key: str,
        step_index: int,
        event_id: str,
        timestamp: float,
        window_seconds: int,
    ) -> list[str]:
        """Record step in a sequence rule and return matched event IDs if sequence completed."""
        client = await self.get_client()
        cutoff = timestamp - window_seconds
        member_val = f"{step_index}:{event_id}"

        if client is not None:
            try:
                await client.zadd(key, {member_val: timestamp})
                await client.zremrangebyscore(key, "-inf", cutoff)
                await client.expire(key, window_seconds * 2)

                entries = await client.zrangebyscore(key, cutoff, "+inf")
                steps_found: dict[int, str] = {}
                for entry in entries:
                    parts = entry.split(":", 1)
                    s_idx = int(parts[0])
                    eid = parts[1]
                    steps_found[s_idx] = eid
                return [steps_found[k] for k in sorted(steps_found.keys())]
            except Exception:
                SlidingWindowCounter._redis_available = False

        # Memory fallback
        store = self._mem_store[key]
        store.append((timestamp, str(step_index), event_id))
        store = [item for item in store if item[0] >= cutoff]
        self._mem_store[key] = store

        steps_found = {}
        for item in store:
            s_idx = int(item[1])
            steps_found[s_idx] = item[2]
        return [steps_found[k] for k in sorted(steps_found.keys())]
