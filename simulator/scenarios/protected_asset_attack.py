"""Scenario: Attack targeting Tier-0 Protected Domain Controller."""

from __future__ import annotations

from typing import Any
from simulator.event_factory import create_event


def get_scenario_events() -> list[dict[str, Any]]:
    """Generates attack events targeting protected asset dc-primary.corp.

    Expected behavior: High-impact host isolation action goes to AWAITING_APPROVAL
    because dc-primary.corp is flagged is_protected=True with Criticality 5.
    """
    events = []
    target_host = "dc-primary.corp"
    attacker_ip = "198.51.100.42"

    # 1. Encoded PowerShell on Domain Controller
    events.append(
        create_event(
            event_type="process_started",
            source="endpoint",
            host=target_host,
            process_name="powershell.exe",
            command_line="powershell.exe -enc JABjAGwAaQBlAG4AdAAgAD0AIABOAGUAdwAtAE8AYgBqAGUAYwB0AA==",
            src_ip=attacker_ip,
            severity_hint=9,
        )
    )

    return events
