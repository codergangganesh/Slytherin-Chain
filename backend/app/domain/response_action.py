"""Domain model for Response Actions and execution state."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID

from app.domain.enums import ActionStatus, ActionType


@dataclass(frozen=True)
class GuardrailDecision:
    """Record of an individual guardrail evaluation for an action."""

    guardrail_name: str
    passed: bool
    reason: str
    evaluated_at: datetime


@dataclass(frozen=True)
class ResponseAction:
    """Represents an automated or human-approved response action."""

    id: UUID
    incident_id: UUID
    action_type: ActionType
    target: str
    status: ActionStatus
    idempotency_key: str
    parameters: dict[str, str | int | float | bool]
    guardrail_decisions: list[GuardrailDecision]
    created_at: datetime
    updated_at: datetime
    ttl_seconds: int | None = None
    expires_at: datetime | None = None
    executed_at: datetime | None = None
    rolled_back_at: datetime | None = None
    approved_by: str | None = None
    denial_reason: str | None = None
    rollback_reason: str | None = None
    execution_result: dict[str, str | int | float | bool] = field(default_factory=dict)
    retry_count: int = 0
