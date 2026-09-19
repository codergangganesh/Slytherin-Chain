"""Event factory for generating realistic attack scenario events."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
import uuid


def create_event(
    event_type: str,
    source: str = "simulator",
    host: str | None = None,
    username: str | None = None,
    src_ip: str | None = None,
    dst_ip: str | None = None,
    dst_port: int | None = None,
    process_name: str | None = None,
    command_line: str | None = None,
    file_path: str | None = None,
    file_hash: str | None = None,
    bytes_out: int | None = None,
    http_path: str | None = None,
    severity_hint: int = 5,
    raw_extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Create a standardized event dictionary."""
    return {
        "event_id": str(uuid.uuid4()),
        "occurred_at": datetime.now(timezone.utc).isoformat(),
        "source": source,
        "event_type": event_type,
        "host": host,
        "username": username,
        "src_ip": src_ip,
        "dst_ip": dst_ip,
        "dst_port": dst_port,
        "process_name": process_name,
        "command_line": command_line,
        "file_path": file_path,
        "file_hash_sha256": file_hash,
        "bytes_out": bytes_out,
        "http_path": http_path,
        "severity_hint": severity_hint,
        "raw": raw_extra or {},
    }
