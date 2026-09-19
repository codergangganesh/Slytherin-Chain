"""Independent CLI verifier for SentinelChain audit-trail integrity.

This script performs independent cryptographic auditing directly against
the database without importing application code paths.

Usage:
    python -m scripts.verify_integrity_cli [--db-url DB_URL]
"""

from __future__ import annotations

import argparse
import asyncio
from datetime import datetime, timezone
import hashlib
import json
import os
import sys
from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

GENESIS_PREVIOUS_HASH = "0" * 64


def _canonical_json(data: Any) -> bytes:
    """Independent canonical JSON serializer."""
    def _default(obj: Any) -> Any:
        if isinstance(obj, datetime):
            if obj.tzinfo is None:
                obj = obj.replace(tzinfo=timezone.utc)
            else:
                obj = obj.astimezone(timezone.utc)
            return obj.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        elif isinstance(obj, UUID):
            return str(obj)
        elif hasattr(obj, "value"):
            return str(obj.value)
        raise TypeError(f"Not serializable: {type(obj)}")

    raw = json.dumps(data, sort_keys=True, separators=(",", ":"), default=_default, ensure_ascii=False)
    return raw.encode("utf-8")


def _compute_hash(seq: int, entry_type: str, inc_id: str | None, payload: Any, created_at: datetime, prev_hash: str) -> str:
    """Independent hash computation."""
    d = {
        "sequence_number": seq,
        "entry_type": str(entry_type),
        "incident_id": str(inc_id) if inc_id else None,
        "payload": payload,
        "created_at": created_at,
    }
    return hashlib.sha256(_canonical_json(d) + prev_hash.encode("utf-8")).hexdigest()


async def verify_audit_ledger(db_url: str) -> bool:
    """Walk and verify hash chain integrity directly in the database."""
    print("=" * 60)
    print(" SentinelChain Independent Integrity Verifier")
    print("=" * 60)
    print(f"Connecting to database: {db_url}...")

    connect_args = {}
    if "sqlite" in db_url:
        connect_args["check_same_thread"] = False

    engine = create_async_engine(db_url, connect_args=connect_args)

    async with engine.connect() as conn:
        result = await conn.execute(text(
            "SELECT sequence_number, entry_type, incident_id, payload, created_at, previous_hash, entry_hash "
            "FROM audit_ledger_entries ORDER BY sequence_number ASC"
        ))
        rows = result.fetchall()

        if not rows:
            print("\n[✔] Status: VERIFIED (Ledger is empty, Genesis state).")
            return True

        print(f"\nAuditing {len(rows)} ledger entries...")
        expected_prev = GENESIS_PREVIOUS_HASH

        for row in rows:
            seq = row[0]
            entry_type = row[1]
            inc_id = row[2]
            payload = row[3]
            if isinstance(payload, str):
                payload = json.loads(payload)
            created_at = row[4]
            prev_hash = row[5]
            entry_hash = row[6]

            if prev_hash != expected_prev:
                print(f"\n[✖] INTEGRITY VIOLATION DETECTED!")
                print(f"    Location: Sequence #{seq}")
                print(f"    Reason: Broken previous hash link.")
                print(f"    Expected: {expected_prev}")
                print(f"    Found:    {prev_hash}")
                return False

            recomputed = _compute_hash(seq, entry_type, inc_id, payload, created_at, prev_hash)
            if recomputed != entry_hash:
                print(f"\n[✖] INTEGRITY VIOLATION DETECTED!")
                print(f"    Location: Sequence #{seq} ({entry_type})")
                print(f"    Reason: Payload modification detected!")
                print(f"    Stored Hash:     {entry_hash}")
                print(f"    Recomputed Hash: {recomputed}")
                return False

            expected_prev = entry_hash

        print(f"\n[✔] SUCCESS: VERIFIED! All {len(rows)} entries cryptographically intact.")
        print(f"    Chain Head Hash: {rows[-1][6]}")
        return True


def main() -> None:
    parser = argparse.ArgumentParser(description="Independent Audit Ledger Verifier")
    parser.add_argument(
        "--db-url",
        default=os.getenv(
            "DATABASE_URL",
            "postgresql+asyncpg://sentinelchain:sentinelchain_dev_password@localhost:5432/sentinelchain"
        ),
        help="Database connection URL",
    )
    args = parser.parse_args()
    success = asyncio.run(verify_audit_ledger(args.db_url))
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
