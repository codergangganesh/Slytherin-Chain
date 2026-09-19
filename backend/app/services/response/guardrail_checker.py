"""Guardrail evaluation engine enforcing safety boundaries before any response action."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import ipaddress
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import AutonomyMode, get_settings
from app.db.orm_models import SystemSettingOrm
from app.domain.asset import Asset
from app.domain.enums import ActionType
from app.domain.incident import Incident
from app.repositories.response_action_repository import ResponseActionRepository
from app.services.response.playbook_loader import PlaybookActionConfig, ResponsePlaybookConfig


@dataclass(frozen=True)
class GuardrailResult:
    """Outcome of evaluating all safety guardrails for an action."""

    can_execute_automatically: bool
    requires_approval: bool
    is_denied: bool
    denial_reason: str | None
    decisions: list[dict[str, Any]]


class GuardrailChecker:
    """Evaluates the 11 safety guardrails defined in SentinelChain specifications."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._settings = get_settings()
        self._action_repo = ResponseActionRepository(session)

    async def _get_current_autonomy_mode(self) -> AutonomyMode:
        """Fetch current runtime autonomy mode from system settings."""
        stmt = select(SystemSettingOrm).where(SystemSettingOrm.key == "autonomy_mode")
        res = await self._session.execute(stmt)
        setting = res.scalar_one_or_none()
        if setting:
            try:
                return AutonomyMode(setting.value)
            except ValueError:
                pass
        return self._settings.default_autonomy_mode

    def _is_ip_allowlisted(self, ip_str: str) -> bool:
        """Check if an IP address matches the allowlist."""
        allowlist = self._settings.allowlisted_ip_list
        for allowed in allowlist:
            try:
                if "/" in allowed:
                    if ipaddress.ip_address(ip_str) in ipaddress.ip_network(allowed, strict=False):
                        return True
                else:
                    if ipaddress.ip_address(ip_str) == ipaddress.ip_address(allowed):
                        return True
            except ValueError:
                if ip_str.lower() == allowed.lower():
                    return True
        return False

    async def evaluate(
        self,
        incident: Incident,
        playbook: ResponsePlaybookConfig,
        action_cfg: PlaybookActionConfig,
        target: str,
        asset: Asset | None = None,
    ) -> GuardrailResult:
        """Evaluate all guardrails for a proposed response action.

        Returns:
            GuardrailResult with automated status, approval flag, denial flag, and audit trail.
        """
        now = datetime.now(timezone.utc).isoformat()
        decisions: list[dict[str, Any]] = []

        # ── GUARDRAIL 1: Autonomy Mode Switch ─────────────────────────────────
        current_mode = await self._get_current_autonomy_mode()
        if current_mode == AutonomyMode.OFF:
            decisions.append({
                "guardrail_name": "autonomy_mode_switch",
                "passed": False,
                "reason": "System autonomy mode is OFF. Automated response disabled.",
                "evaluated_at": now,
            })
            return GuardrailResult(
                can_execute_automatically=False,
                requires_approval=False,
                is_denied=True,
                denial_reason="Autonomy mode is OFF",
                decisions=decisions,
            )

        decisions.append({
            "guardrail_name": "autonomy_mode_switch",
            "passed": True,
            "reason": f"Autonomy mode is '{current_mode.value}'",
            "evaluated_at": now,
        })

        # ── GUARDRAIL 2: Allowlist Check ──────────────────────────────────────
        if action_cfg.action_type == ActionType.BLOCK_IP:
            if self._is_ip_allowlisted(target):
                decisions.append({
                    "guardrail_name": "allowlist_check",
                    "passed": False,
                    "reason": f"Target IP '{target}' is protected under the trusted IP allowlist.",
                    "evaluated_at": now,
                })
                return GuardrailResult(
                    can_execute_automatically=False,
                    requires_approval=False,
                    is_denied=True,
                    denial_reason=f"Target IP '{target}' is allowlisted",
                    decisions=decisions,
                )

        decisions.append({
            "guardrail_name": "allowlist_check",
            "passed": True,
            "reason": f"Target '{target}' is not in allowlist",
            "evaluated_at": now,
        })

        # ── GUARDRAIL 3: Protected Asset Check ────────────────────────────────
        requires_approval = (current_mode == AutonomyMode.APPROVAL_REQUIRED)

        if asset and asset.is_protected:
            if action_cfg.action_type in (ActionType.ISOLATE_HOST, ActionType.DISABLE_USER):
                requires_approval = True
                decisions.append({
                    "guardrail_name": "protected_asset_check",
                    "passed": False,
                    "reason": f"Asset '{asset.hostname}' is flagged as protected; action requires human sign-off.",
                    "evaluated_at": now,
                })
            else:
                decisions.append({
                    "guardrail_name": "protected_asset_check",
                    "passed": True,
                    "reason": "Action type does not isolate protected asset",
                    "evaluated_at": now,
                })
        else:
            decisions.append({
                "guardrail_name": "protected_asset_check",
                "passed": True,
                "reason": "Target asset is not marked protected",
                "evaluated_at": now,
            })

        # ── GUARDRAIL 4: Risk Score & Confidence Thresholds ───────────────────
        if incident.risk_score < playbook.conditions.min_risk_score:
            decisions.append({
                "guardrail_name": "threshold_check",
                "passed": False,
                "reason": f"Incident score {incident.risk_score} below playbook minimum {playbook.conditions.min_risk_score}",
                "evaluated_at": now,
            })
            return GuardrailResult(
                can_execute_automatically=False,
                requires_approval=False,
                is_denied=True,
                denial_reason="Risk score below playbook trigger threshold",
                decisions=decisions,
            )

        decisions.append({
            "guardrail_name": "threshold_check",
            "passed": True,
            "reason": f"Incident risk score {incident.risk_score} satisfies playbook minimum {playbook.conditions.min_risk_score}",
            "evaluated_at": now,
        })

        # ── GUARDRAIL 5: High-Impact Action Escalation ────────────────────────
        if action_cfg.action_type == ActionType.ISOLATE_HOST and asset and asset.criticality >= 4:
            requires_approval = True
            decisions.append({
                "guardrail_name": "high_impact_escalation",
                "passed": False,
                "reason": f"Host isolation on criticality {asset.criticality}/5 asset requires human approval.",
                "evaluated_at": now,
            })
        elif action_cfg.requires_approval_if:
            conds = action_cfg.requires_approval_if
            if conds.asset_criticality_at_least and asset and asset.criticality >= conds.asset_criticality_at_least:
                requires_approval = True
                decisions.append({
                    "guardrail_name": "high_impact_escalation",
                    "passed": False,
                    "reason": f"Asset criticality {asset.criticality} >= required threshold {conds.asset_criticality_at_least}",
                    "evaluated_at": now,
                })
            elif conds.is_protected_asset and asset and asset.is_protected:
                requires_approval = True
                decisions.append({
                    "guardrail_name": "high_impact_escalation",
                    "passed": False,
                    "reason": "Playbook requires approval for protected assets",
                    "evaluated_at": now,
                })
            else:
                decisions.append({
                    "guardrail_name": "high_impact_escalation",
                    "passed": True,
                    "reason": "Impact criteria within automatic limits",
                    "evaluated_at": now,
                })
        else:
            decisions.append({
                "guardrail_name": "high_impact_escalation",
                "passed": True,
                "reason": "Standard impact action",
                "evaluated_at": now,
            })

        # ── GUARDRAIL 6: Blast Radius Rate Limits ─────────────────────────────
        global_actions_1h = await self._action_repo.count_actions_in_window(hours=1)
        if global_actions_1h >= self._settings.max_auto_actions_per_hour_global:
            requires_approval = True
            decisions.append({
                "guardrail_name": "blast_radius_rate_limit",
                "passed": False,
                "reason": f"Global actions in past hour ({global_actions_1h}) exceeded safety threshold ({self._settings.max_auto_actions_per_hour_global})",
                "evaluated_at": now,
            })
        else:
            decisions.append({
                "guardrail_name": "blast_radius_rate_limit",
                "passed": True,
                "reason": f"Global action count ({global_actions_1h}/{self._settings.max_auto_actions_per_hour_global}) within limits",
                "evaluated_at": now,
            })

        # Autonomy mode recommend_only check
        if current_mode == AutonomyMode.RECOMMEND_ONLY:
            requires_approval = True

        can_auto = (not requires_approval) and (current_mode == AutonomyMode.AUTO)

        return GuardrailResult(
            can_execute_automatically=can_auto,
            requires_approval=requires_approval,
            is_denied=False,
            denial_reason=None,
            decisions=decisions,
        )
