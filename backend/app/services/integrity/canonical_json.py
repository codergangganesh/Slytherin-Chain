"""Deterministic Canonical JSON serialization for cryptographic integrity."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any
from uuid import UUID


def _json_default(obj: Any) -> Any:
    """Serialize custom types into deterministic JSON representations."""
    if isinstance(obj, (datetime,)):
        # Normalize to UTC ISO-8601 with trailing Z
        if obj.tzinfo is None:
            obj = obj.replace(tzinfo=UTC)
        else:
            obj = obj.astimezone(UTC)
        return obj.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    elif isinstance(obj, UUID):
        return str(obj)
    elif hasattr(obj, "value"):
        return str(obj.value)
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


def canonicalize(data: Any) -> str:
    """Serialize any data structure into canonical JSON.

    Properties:
        - Keys strictly sorted alphabetically
        - No unnecessary whitespace (separators: ',' and ':')
        - UTF-8 deterministic encoding
        - Standardized ISO-8601 UTC timestamp formatting
    """
    return json.dumps(
        data,
        sort_keys=True,
        separators=(",", ":"),
        default=_json_default,
        ensure_ascii=False,
    )


def canonical_bytes(data: Any) -> bytes:
    """Serialize canonical JSON to UTF-8 encoded bytes."""
    return canonicalize(data).encode("utf-8")
