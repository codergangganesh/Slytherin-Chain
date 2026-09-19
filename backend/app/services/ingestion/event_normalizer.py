"""Event normalization service.

Converts various raw log formats (SSH, Web, Endpoint, Firewall, Simulator)
into the standard ECS-aligned NormalizedEvent domain model.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
import uuid

from app.domain.enums import EventSource, EventType
from app.domain.normalized_event import NormalizedEvent


class EventNormalizer:
    """Normalizes heterogenous security event formats into a uniform representation."""

    @staticmethod
    def normalize(raw_payload: dict[str, Any]) -> NormalizedEvent:
        """Normalize a single raw event dictionary.

        Args:
            raw_payload: Input dictionary containing raw log data or pre-normalized fields.

        Returns:
            NormalizedEvent: Strongly-typed normalized domain entity.
        """
        now = datetime.now(timezone.utc)

        # Parse event_id or generate a new UUID
        raw_id = raw_payload.get("event_id")
        event_id = uuid.UUID(str(raw_id)) if raw_id else uuid.uuid4()

        # Parse occurred_at timestamp
        occurred_at_raw = raw_payload.get("occurred_at") or raw_payload.get("timestamp")
        if occurred_at_raw:
            if isinstance(occurred_at_raw, datetime):
                occurred_at = occurred_at_raw
            else:
                try:
                    occurred_at = datetime.fromisoformat(str(occurred_at_raw).replace("Z", "+00:00"))
                except ValueError:
                    occurred_at = now
        else:
            occurred_at = now

        # Normalize EventSource
        source_raw = str(raw_payload.get("source", "simulator")).lower()
        try:
            source = EventSource(source_raw)
        except ValueError:
            source = EventSource.SIMULATOR

        # Normalize EventType
        type_raw = str(raw_payload.get("event_type", "login_failed")).lower()
        try:
            event_type = EventType(type_raw)
        except ValueError:
            event_type = EventType.LOGIN_FAILED

        # Extract normalized attributes
        host = raw_payload.get("host")
        username = raw_payload.get("username")
        src_ip = raw_payload.get("src_ip")
        dst_ip = raw_payload.get("dst_ip")
        dst_port = raw_payload.get("dst_port")
        if dst_port is not None:
            try:
                dst_port = int(dst_port)
            except (ValueError, TypeError):
                dst_port = None

        process_name = raw_payload.get("process_name")
        command_line = raw_payload.get("command_line")
        file_path = raw_payload.get("file_path")
        file_hash_sha256 = raw_payload.get("file_hash_sha256")
        
        bytes_out = raw_payload.get("bytes_out")
        if bytes_out is not None:
            try:
                bytes_out = int(bytes_out)
            except (ValueError, TypeError):
                bytes_out = None

        http_path = raw_payload.get("http_path")
        severity_hint = raw_payload.get("severity_hint")
        if severity_hint is not None:
            try:
                severity_hint = int(severity_hint)
            except (ValueError, TypeError):
                severity_hint = None

        raw_data = raw_payload.get("raw") if isinstance(raw_payload.get("raw"), dict) else raw_payload

        return NormalizedEvent(
            event_id=event_id,
            occurred_at=occurred_at,
            ingested_at=now,
            source=source,
            event_type=event_type,
            host=str(host) if host else None,
            username=str(username) if username else None,
            src_ip=str(src_ip) if src_ip else None,
            dst_ip=str(dst_ip) if dst_ip else None,
            dst_port=dst_port,
            process_name=str(process_name) if process_name else None,
            command_line=str(command_line) if command_line else None,
            file_path=str(file_path) if file_path else None,
            file_hash_sha256=str(file_hash_sha256) if file_hash_sha256 else None,
            bytes_out=bytes_out,
            http_path=str(http_path) if http_path else None,
            severity_hint=severity_hint,
            raw=raw_data,
        )
