"""Scenario: SSH Brute Force with Valid Account Compromise and Exfiltration."""

from __future__ import annotations

from typing import Any
from simulator.event_factory import create_event


def get_scenario_events() -> list[dict[str, Any]]:
    """Generates the multi-step SSH brute force compromisation event sequence."""
    events = []
    attacker_ip = "198.51.100.42"
    target_host = "web-prod-01.corp"
    target_user = "root"

    # 1. 6 Failed login attempts
    for i in range(6):
        events.append(
            create_event(
                event_type="login_failed",
                source="ssh",
                host=target_host,
                username=target_user,
                src_ip=attacker_ip,
                dst_port=22,
                severity_hint=6,
                raw_extra={"attempt": i + 1, "service": "sshd"},
            )
        )

    # 2. 1 Successful login (Sequence trigger)
    events.append(
        create_event(
            event_type="login_success",
            source="ssh",
            host=target_host,
            username=target_user,
            src_ip=attacker_ip,
            dst_port=22,
            severity_hint=8,
            raw_extra={"message": "Accepted password for root"},
        )
    )

    # 3. New admin user creation
    events.append(
        create_event(
            event_type="user_created",
            source="endpoint",
            host=target_host,
            username="backdoor_admin",
            src_ip=attacker_ip,
            command_line="useradd -m -s /bin/bash -G sudo backdoor_admin",
            severity_hint=7,
        )
    )

    # 4. Large outbound data exfiltration transfer
    events.append(
        create_event(
            event_type="outbound_transfer",
            source="firewall",
            host=target_host,
            src_ip=attacker_ip,
            dst_ip="203.0.113.88",
            dst_port=443,
            bytes_out=15728640,  # 15 MB
            severity_hint=8,
        )
    )

    return events
