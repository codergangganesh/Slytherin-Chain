"""Simulates audit trail tampering by modifying a stored database row directly.

Usage:
    python -m scripts.simulate_tampering [--sequence SEQ]
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine


async def tamper_database(seq_num: int | None, db_url: str) -> None:
    """Modify a payload in audit_ledger_entries directly."""
    print("=" * 60)
    print(" SentinelChain Database Tamper Simulation Tool")
    print("=" * 60)

    connect_args = {}
    if "sqlite" in db_url:
        connect_args["check_same_thread"] = False

    engine = create_async_engine(db_url, connect_args=connect_args)

    async with engine.connect() as conn:
        # Find target sequence
        if seq_num is None:
            res = await conn.execute(text("SELECT sequence_number FROM audit_ledger_entries ORDER BY sequence_number ASC LIMIT 1"))
            row = res.fetchone()
            if not row:
                print("[!] Error: No audit ledger entries exist to tamper with. Run a simulation scenario first!")
                return
            target_seq = row[0]
        else:
            target_seq = seq_num

        print(f"[*] Attacking sequence #{target_seq}...")
        # Direct SQL UPDATE altering payload content without updating entry_hash
        malicious_payload = json.dumps({
            "tampered_by": "attacker",
            "malicious_modification": "Covering tracks by erasing attacker IP",
            "altered_timestamp": "2026-09-19T00:00:00Z",
        })

        await conn.execute(
            text("UPDATE audit_ledger_entries SET payload = :p WHERE sequence_number = :s"),
            {"p": malicious_payload, "s": target_seq},
        )
        await conn.commit()
        print(f"[✔] Tampering complete! Modified record #{target_seq} directly in database.")
        print("[*] Now run 'python -m scripts.verify_integrity_cli' or click 'Verify now' in the UI to see the cryptographic tamper detection.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Simulate Database Tampering")
    parser.add_argument("--sequence", type=int, default=None, help="Sequence number to tamper")
    parser.add_argument(
        "--db-url",
        default=os.getenv(
            "DATABASE_URL",
            "postgresql+asyncpg://sentinelchain:sentinelchain_dev_password@localhost:5432/sentinelchain"
        ),
        help="Database connection URL",
    )
    args = parser.parse_args()
    asyncio.run(tamper_database(args.sequence, args.db_url))


if __name__ == "__main__":
    main()
