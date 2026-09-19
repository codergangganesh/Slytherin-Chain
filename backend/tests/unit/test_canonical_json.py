"""Unit tests for deterministic canonical JSON serialization."""

from __future__ import annotations

from datetime import datetime, timezone
import uuid

from app.services.integrity.canonical_json import canonical_bytes, canonicalize


def test_canonical_json_key_sorting() -> None:
    """Test that object keys are sorted strictly alphabetically."""
    data1 = {"z": 1, "a": 2, "m": 3}
    data2 = {"a": 2, "m": 3, "z": 1}
    assert canonicalize(data1) == '{"a":2,"m":3,"z":1}'
    assert canonicalize(data1) == canonicalize(data2)


def test_canonical_json_datetime_and_uuid_formatting() -> None:
    """Test standard UTC ISO-8601 formatting and UUID string serialization."""
    dt = datetime(2026, 9, 19, 10, 0, 0, tzinfo=timezone.utc)
    uid = uuid.UUID("12345678-1234-5678-1234-567812345678")
    data = {"timestamp": dt, "id": uid, "status": "active"}

    output = canonicalize(data)
    expected = '{"id":"12345678-1234-5678-1234-567812345678","status":"active","timestamp":"2026-09-19T10:00:00.000000Z"}'
    assert output == expected


def test_canonical_bytes_determinism() -> None:
    """Test that canonical_bytes returns exact byte match."""
    data = {"action": "block_ip", "target": "198.51.100.42", "ttl": 3600}
    b1 = canonical_bytes(data)
    b2 = canonical_bytes({"ttl": 3600, "action": "block_ip", "target": "198.51.100.42"})
    assert b1 == b2
    assert isinstance(b1, bytes)
