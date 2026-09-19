"""Executive summary generator with template logic and optional LLM integration."""

from __future__ import annotations

from typing import Any

from app.config.settings import get_settings


class ExecutiveSummaryGenerator:
    """Generates structured, professional executive summaries for incident reports."""

    def __init__(self) -> None:
        self._settings = get_settings()

    def generate_summary(
        self,
        reference_id: str,
        title: str,
        priority: str,
        risk_score: float,
        tactics: list[str],
        primary_attacker: str | None,
        primary_target: str | None,
        actions_taken: list[dict[str, Any]],
        status: str,
    ) -> str:
        """Generate a clean, deterministic template-based executive summary."""
        tactic_str = ", ".join(tactics) if tactics else "Unclassified activity"
        attacker_str = f"originating from {primary_attacker}" if primary_attacker else "from an unconfirmed source"
        target_str = f"targeting {primary_target}" if primary_target else "impacting monitored systems"

        action_summary = "No active containment was required."
        if actions_taken:
            exec_actions = [f"{a.get('action_type')} on {a.get('target')}" for a in actions_taken if a.get("status") == "SUCCEEDED"]
            if exec_actions:
                action_summary = f"Autonomous and approved containment actions executed: {'; '.join(exec_actions)}."
            else:
                action_summary = f"Actions evaluated: {len(actions_taken)} actions proposed/denied by safety guardrails."

        summary = (
            f"On detection of {title} ({reference_id}), the platform classified the threat as {priority} priority "
            f"with an explainable risk score of {risk_score}/100. The incident exhibited {tactic_str} patterns {attacker_str}, {target_str}. "
            f"{action_summary} Current incident operational state: {status}."
        )
        return summary
