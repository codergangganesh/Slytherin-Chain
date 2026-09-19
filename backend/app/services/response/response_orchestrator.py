"""Autonomous response orchestrator and action lifecycle manager."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.enforcement.simulated_firewall_connector import SimulatedFirewallConnector
from app.adapters.enforcement.simulated_identity_connector import SimulatedIdentityConnector
from app.domain.enums import ActionStatus, ActionType, EntryType, IncidentStatus
from app.domain.exceptions import EntityNotFoundError
from app.domain.incident import Incident
from app.domain.response_action import ResponseAction
from app.repositories.asset_repository import AssetRepository
from app.repositories.incident_repository import IncidentRepository
from app.repositories.response_action_repository import ResponseActionRepository
from app.services.integrity.hash_chain_ledger import HashChainLedger
from app.services.response.guardrail_checker import GuardrailChecker
from app.services.response.playbook_loader import PlaybookLoader, ResponsePlaybookConfig


class ResponseOrchestrator:
    """Orchestrates response playbook matching, guardrail verification, and action execution."""

    def __init__(
        self,
        session: AsyncSession,
        playbooks: list[ResponsePlaybookConfig] | None = None,
        playbooks_directory: Path | None = None,
    ) -> None:
        self._session = session
        self._action_repo = ResponseActionRepository(session)
        self._incident_repo = IncidentRepository(session)
        self._asset_repo = AssetRepository(session)
        self._guardrail_checker = GuardrailChecker(session)
        self._ledger = HashChainLedger(session)
        self._fw_connector = SimulatedFirewallConnector(session)
        self._identity_connector = SimulatedIdentityConnector(session)

        if playbooks is not None:
            self._playbooks = playbooks
        else:
            default_dir = (
                playbooks_directory
                or Path(__file__).resolve().parent.parent.parent.parent / "playbooks"
            )
            self._playbooks = PlaybookLoader.load_from_directory(default_dir)

    def _resolve_target(self, incident: Incident, target_expr: str) -> str | None:
        """Resolve playbook target expression from incident attributes."""
        if target_expr == "incident.primary_src_ip":
            return incident.primary_src_ip
        elif target_expr == "incident.primary_host":
            return incident.primary_host
        elif target_expr == "incident.primary_username":
            return incident.primary_username
        elif target_expr == "webhook":
            return "webhook_notification"
        return target_expr

    def _get_connector_for_action(self, action_type: ActionType) -> Any:
        """Select the appropriate enforcement adapter."""
        if self._fw_connector.supports_action(action_type):
            return self._fw_connector
        return self._identity_connector

    async def evaluate_incident(self, incident: Incident) -> list[ResponseAction]:
        """Match incident against playbooks and execute or queue response actions."""
        actions_taken: list[ResponseAction] = []
        target_asset = None
        if incident.primary_host:
            target_asset = await self._asset_repo.get_by_hostname(incident.primary_host)

        for playbook in self._playbooks:
            # Check playbook category match
            # Playbook applies if category is relevant or general
            for action_cfg in playbook.actions:
                target = self._resolve_target(incident, action_cfg.target)
                if not target:
                    continue

                # Idempotency key: incident_id:action_type:target
                idempotency_key = f"{incident.id}:{action_cfg.action_type.value}:{target}"
                existing = await self._action_repo.get_by_idempotency_key(idempotency_key)
                if existing:
                    continue

                # Guardrail Evaluation
                guardrail_res = await self._guardrail_checker.evaluate(
                    incident=incident,
                    playbook=playbook,
                    action_cfg=action_cfg,
                    target=target,
                    asset=target_asset,
                )

                if guardrail_res.is_denied:
                    # Persist DENIED action for transparency
                    action = await self._action_repo.create(
                        incident_id=incident.id,
                        action_type=action_cfg.action_type,
                        target=target,
                        idempotency_key=idempotency_key,
                        parameters={
                            "action_type": action_cfg.action_type.value,
                            "reason": "Playbook policy",
                        },
                        guardrail_decisions=guardrail_res.decisions,
                        status=ActionStatus.DENIED,
                        denial_reason=guardrail_res.denial_reason,
                    )
                    await self._incident_repo.add_timeline_entry(
                        incident_id=incident.id,
                        entry_type="ACTION_DENIED",
                        title=f"Response Action Denied: {action_cfg.action_type.value} on {target}",
                        description=f"Action denied by guardrails: {guardrail_res.denial_reason}",
                        actor="guardrail_engine",
                        metadata={
                            "action_id": str(action.id),
                            "reason": guardrail_res.denial_reason,
                        },
                    )
                    await self._ledger.append_entry(
                        entry_type=EntryType.ACTION_DENIED,
                        incident_id=incident.id,
                        payload={
                            "action_type": action_cfg.action_type.value,
                            "target": target,
                            "reason": guardrail_res.denial_reason,
                        },
                    )
                    actions_taken.append(action)
                    continue

                if guardrail_res.requires_approval or not guardrail_res.can_execute_automatically:
                    # Escalates to AWAITING_APPROVAL
                    action = await self._action_repo.create(
                        incident_id=incident.id,
                        action_type=action_cfg.action_type,
                        target=target,
                        idempotency_key=idempotency_key,
                        parameters={
                            "action_type": action_cfg.action_type.value,
                            "reason": "Awaiting analyst review",
                        },
                        guardrail_decisions=guardrail_res.decisions,
                        status=ActionStatus.AWAITING_APPROVAL,
                        ttl_seconds=action_cfg.ttl_seconds,
                    )
                    # Update incident status to AWAITING_APPROVAL
                    await self._incident_repo.update_incident(
                        incident_id=incident.id,
                        status=IncidentStatus.AWAITING_APPROVAL,
                    )
                    await self._incident_repo.add_timeline_entry(
                        incident_id=incident.id,
                        entry_type="ACTION_AWAITING_APPROVAL",
                        title=f"Approval Required: {action_cfg.action_type.value} on {target}",
                        description=f"High-impact action {action_cfg.action_type.value} requires human confirmation before execution.",
                        actor="guardrail_engine",
                        metadata={"action_id": str(action.id)},
                    )
                    await self._ledger.append_entry(
                        entry_type=EntryType.ACTION_PROPOSED,
                        incident_id=incident.id,
                        payload={
                            "action_id": str(action.id),
                            "action_type": action_cfg.action_type.value,
                            "target": target,
                        },
                    )
                    actions_taken.append(action)
                    continue

                # Automatic Execution
                action = await self._action_repo.create(
                    incident_id=incident.id,
                    action_type=action_cfg.action_type,
                    target=target,
                    idempotency_key=idempotency_key,
                    parameters={
                        "action_type": action_cfg.action_type.value,
                        "reason": "Autonomous playbook policy",
                    },
                    guardrail_decisions=guardrail_res.decisions,
                    status=ActionStatus.EXECUTING,
                    ttl_seconds=action_cfg.ttl_seconds,
                )

                connector = self._get_connector_for_action(action_cfg.action_type)
                now = datetime.now(UTC)
                try:
                    exec_result = await connector.execute(
                        action_id=action.id,
                        incident_id=incident.id,
                        target=target,
                        parameters={
                            "action_type": action_cfg.action_type.value,
                            "reason": "Autonomous policy",
                        },
                        ttl_seconds=action_cfg.ttl_seconds,
                    )
                    updated_action = await self._action_repo.update_status(
                        action_id=action.id,
                        status=ActionStatus.SUCCEEDED,
                        executed_at=now,
                        execution_result=exec_result,
                    )
                    # Move incident to CONTAINED if containment action succeeded
                    if action_cfg.action_type in (
                        ActionType.BLOCK_IP,
                        ActionType.ISOLATE_HOST,
                        ActionType.DISABLE_USER,
                    ):
                        await self._incident_repo.update_incident(
                            incident_id=incident.id,
                            status=IncidentStatus.CONTAINED,
                        )

                    await self._incident_repo.add_timeline_entry(
                        incident_id=incident.id,
                        entry_type="ACTION_EXECUTED",
                        title=f"Autonomous Action Executed: {action_cfg.action_type.value} on {target}",
                        description=f"Action successfully applied with {action_cfg.ttl_seconds or 'no'}s TTL.",
                        actor="autonomous_response_engine",
                        metadata={
                            "action_id": str(action.id),
                            "ttl_seconds": action_cfg.ttl_seconds,
                        },
                    )
                    await self._ledger.append_entry(
                        entry_type=EntryType.ACTION_EXECUTED,
                        incident_id=incident.id,
                        payload={
                            "action_id": str(action.id),
                            "action_type": action_cfg.action_type.value,
                            "target": target,
                            "result": exec_result,
                        },
                    )
                    if updated_action:
                        actions_taken.append(updated_action)
                except Exception as err:
                    await self._action_repo.update_status(
                        action_id=action.id,
                        status=ActionStatus.FAILED,
                        denial_reason=str(err),
                    )
                    await self._ledger.append_entry(
                        entry_type=EntryType.ACTION_FAILED,
                        incident_id=incident.id,
                        payload={"action_id": str(action.id), "error": str(err)},
                    )

        return actions_taken

    async def approve_action(self, action_id: UUID, approver_username: str) -> ResponseAction:
        """Manually approve and execute a pending response action."""
        action = await self._action_repo.get_by_id(action_id)
        if not action:
            raise EntityNotFoundError("ResponseAction", str(action_id))

        now = datetime.now(UTC)
        connector = self._get_connector_for_action(action.action_type)
        exec_result = await connector.execute(
            action_id=action.id,
            incident_id=action.incident_id,
            target=action.target,
            parameters=action.parameters,
            ttl_seconds=action.ttl_seconds,
        )

        updated = await self._action_repo.update_status(
            action_id=action.id,
            status=ActionStatus.SUCCEEDED,
            executed_at=now,
            approved_by=approver_username,
            execution_result=exec_result,
        )

        # Move incident to CONTAINED
        if action.action_type in (
            ActionType.BLOCK_IP,
            ActionType.ISOLATE_HOST,
            ActionType.DISABLE_USER,
        ):
            await self._incident_repo.update_incident(
                incident_id=action.incident_id,
                status=IncidentStatus.CONTAINED,
            )

        await self._incident_repo.add_timeline_entry(
            incident_id=action.incident_id,
            entry_type="ACTION_APPROVED",
            title=f"Action Approved: {action.action_type.value} on {action.target}",
            description=f"Action approved by {approver_username} and successfully executed.",
            actor=f"user:{approver_username}",
            metadata={"action_id": str(action.id), "approver": approver_username},
        )
        await self._ledger.append_entry(
            entry_type=EntryType.ACTION_APPROVED,
            incident_id=action.incident_id,
            payload={"action_id": str(action.id), "approved_by": approver_username},
        )

        assert updated is not None
        return updated

    async def deny_action(
        self, action_id: UUID, denier_username: str, reason: str
    ) -> ResponseAction:
        """Manually deny a pending response action."""
        action = await self._action_repo.get_by_id(action_id)
        if not action:
            raise EntityNotFoundError("ResponseAction", str(action_id))

        updated = await self._action_repo.update_status(
            action_id=action.id,
            status=ActionStatus.DENIED,
            approved_by=denier_username,
            denial_reason=reason,
        )

        await self._incident_repo.add_timeline_entry(
            incident_id=action.incident_id,
            entry_type="ACTION_DENIED",
            title=f"Action Denied by Analyst: {action.action_type.value} on {action.target}",
            description=f"Denial Reason: {reason}",
            actor=f"user:{denier_username}",
            metadata={"action_id": str(action.id), "denier": denier_username, "reason": reason},
        )
        await self._ledger.append_entry(
            entry_type=EntryType.ACTION_DENIED,
            incident_id=action.incident_id,
            payload={"action_id": str(action.id), "denied_by": denier_username, "reason": reason},
        )

        assert updated is not None
        return updated

    async def rollback_action(
        self, action_id: UUID, actor_username: str, reason: str
    ) -> ResponseAction:
        """Revert a previously executed response action."""
        action = await self._action_repo.get_by_id(action_id)
        if not action:
            raise EntityNotFoundError("ResponseAction", str(action_id))

        now = datetime.now(UTC)
        connector = self._get_connector_for_action(action.action_type)
        await connector.rollback(
            action_id=action.id,
            target=action.target,
            parameters=action.parameters,
        )

        updated = await self._action_repo.update_status(
            action_id=action.id,
            status=ActionStatus.ROLLED_BACK,
            rolled_back_at=now,
            rollback_reason=reason,
        )

        await self._incident_repo.add_timeline_entry(
            incident_id=action.incident_id,
            entry_type="ACTION_ROLLED_BACK",
            title=f"Action Rolled Back: {action.action_type.value} on {action.target}",
            description=f"Rollback reason: {reason}",
            actor=f"user:{actor_username}",
            metadata={"action_id": str(action.id), "reason": reason},
        )
        await self._ledger.append_entry(
            entry_type=EntryType.ACTION_ROLLED_BACK,
            incident_id=action.incident_id,
            payload={
                "action_id": str(action.id),
                "rolled_back_by": actor_username,
                "reason": reason,
            },
        )

        assert updated is not None
        return updated

    async def dry_run_action(self, action_type: ActionType, target: str) -> dict[str, Any]:
        """Perform a dry-run simulation of an action."""
        connector = self._get_connector_for_action(action_type)
        return await connector.dry_run(target, {"action_type": action_type.value})
