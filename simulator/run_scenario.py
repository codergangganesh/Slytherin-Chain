"""Scenario runner CLI tool for SentinelChain Attack Simulator.

Usage:
    python -m simulator.run_scenario ssh_brute_force_compromise [--speed SPEED] [--api-url URL] [--api-key KEY]
"""

from __future__ import annotations

import argparse
import asyncio
import importlib
import os
import sys
import time
from typing import Any

import httpx


def load_scenario(scenario_name: str) -> list[dict[str, Any]]:
    """Dynamically load scenario module and return events."""
    try:
        mod = importlib.import_module(f"simulator.scenarios.{scenario_name}")
        return mod.get_scenario_events()
    except ModuleNotFoundError as err:
        print(f"[!] Error: Scenario '{scenario_name}' not found. Available scenarios:")
        for name in [
            "ssh_brute_force_compromise",
            "port_scan_recon",
            "ransomware_activity",
            "benign_admin_scan_false_positive",
            "protected_asset_attack",
        ]:
            print(f"    - {name}")
        sys.exit(1)


async def run_scenario_cli(
    scenario_name: str,
    speed: float = 1.0,
    api_url: str = "http://localhost:8000/api/v1/events",
    api_key: str = "sentinelchain-demo-api-key",
) -> None:
    """Execute scenario by sending events via HTTP API."""
    events = load_scenario(scenario_name)
    print("=" * 60)
    print(f" SentinelChain Attack Simulator — Scenario: {scenario_name}")
    print("=" * 60)
    print(f"Posting {len(events)} events to {api_url} at {speed}x speed multiplier...")

    delay_between_events = max(0.05, 0.5 / speed)

    async with httpx.AsyncClient(timeout=10.0) as client:
        for idx, event in enumerate(events, 1):
            headers = {"X-API-Key": api_key, "Content-Type": "application/json"}
            try:
                resp = await client.post(api_url, json=event, headers=headers)
                if resp.status_code in (200, 201, 202):
                    print(f"  [{idx}/{len(events)}] Sent {event.get('event_type')} ({event.get('src_ip') or event.get('host')}) -> HTTP {resp.status_code}")
                else:
                    print(f"  [{idx}/{len(events)}] Ingestion error: HTTP {resp.status_code} - {resp.text}")
            except Exception as e:
                print(f"  [{idx}/{len(events)}] Network connection error: {e}")

            if idx < len(events):
                await asyncio.sleep(delay_between_events)

    print("\n[✔] Scenario execution complete!")
    print("[*] Open the SentinelChain dashboard to view the generated incident, attack timeline, and autonomous response actions.")


def main() -> None:
    parser = argparse.ArgumentParser(description="SentinelChain Scenario Runner CLI")
    parser.add_argument("scenario", help="Name of the scenario to launch")
    parser.add_argument("--speed", type=float, default=1.0, help="Speed multiplier (e.g. 2.0 for 2x faster)")
    parser.add_argument(
        "--api-url",
        default=os.getenv("INGESTION_API_URL", "http://localhost:8000/api/v1/events"),
        help="Backend ingestion API URL",
    )
    parser.add_argument(
        "--api-key",
        default=os.getenv("INGESTION_API_KEY", "sentinelchain-demo-api-key"),
        help="Ingestion X-API-Key",
    )
    args = parser.parse_args()
    asyncio.run(run_scenario_cli(args.scenario, speed=args.speed, api_url=args.api_url, api_key=args.api_key))


if __name__ == "__main__":
    main()
