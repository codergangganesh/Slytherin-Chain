"""Scenario: Benign Admin scan from allowlisted IP — Guardrail Denial demo."""

from __future__ import annotations

from typing import Any
from simulator.event_factory import create_event


def get_scenario_events() -> list[dict[str, Any]]:
    """Generates failed logins from allowlisted admin IP (10.0.0.1).

    Expected behavior: Rule fires, but Guardrail 2 (Allowlist) DENIES the block action
    and records the denial in the incident timeline and ledger.
    """
    events = []
    admin_ip = "10.0.0.1"  # In default allowlist
    target_host = "web-prod-01.corp"

    for i in range(6):
        events.append(
            create_event(
                event_type="login_failed",
                source="ssh",
                host=target_host,
                username="admin",
                src_ip=admin_ip,
                dst_port=22,
                severity_hint=5,
                raw_extra={"reason": "Admin automated credential audit"},
            )
        )

    return events
