"""Scenario: Port Scan Reconnaissance across multiple destination ports."""

from __future__ import annotations

from typing import Any
from simulator.event_factory import create_event


def get_scenario_events() -> list[dict[str, Any]]:
    """Generates sequential port connection events from a single IP."""
    events = []
    attacker_ip = "192.0.2.15"
    target_host = "web-prod-01.corp"
    ports = [21, 22, 23, 25, 80, 443, 8080, 3389]

    for p in ports:
        events.append(
            create_event(
                event_type="port_connection",
                source="firewall",
                host=target_host,
                src_ip=attacker_ip,
                dst_port=p,
                severity_hint=4,
                raw_extra={"probe": "SYN_SCAN"},
            )
        )

    return events
