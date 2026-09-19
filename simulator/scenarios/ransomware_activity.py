"""Scenario: Ransomware activity on high-criticality asset triggering isolation approval."""

from __future__ import annotations

from typing import Any
from simulator.event_factory import create_event


def get_scenario_events() -> list[dict[str, Any]]:
    """Generates suspicious encoded PowerShell process and mass file modifications."""
    events = []
    target_host = "db-cluster-01.corp"
    attacker_ip = "203.0.113.88"

    # 1. Encoded PowerShell dropper
    events.append(
        create_event(
            event_type="process_started",
            source="endpoint",
            host=target_host,
            process_name="powershell.exe",
            command_line="powershell.exe -enc SQBFAFgAIAAoAE4AZQB3AC0ATwBiAGoAZQBjAHQAIABOAGUAdAAuAFcAZQBiAEMAbABpAGUAbgB0ACkALgBEAG8AdwBuAGwAbwBhAGQAUwB0AHIAaQBuAGcAKAApAA==",
            src_ip=attacker_ip,
            severity_hint=9,
        )
    )

    # 2. Mass file encryption (files modified rapidly)
    for i in range(6):
        events.append(
            create_event(
                event_type="file_modified",
                source="endpoint",
                host=target_host,
                file_path=f"/var/lib/data/finance_records_{i}.db.locked",
                file_hash="a1b2c3d4e5f67890123456789abcdef0123456789abcdef0123456789abcdef0",
                severity_hint=10,
                raw_extra={"extension": ".locked"},
            )
        )

    return events
