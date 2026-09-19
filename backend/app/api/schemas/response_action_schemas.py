"""Response action request and response schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID
from pydantic import BaseModel, Field

from app.domain.enums import ActionStatus, ActionType


class GuardrailDecisionSchema(BaseModel):
    """Schema representing an individual guardrail evaluation."""

    guardrail_name: str
    passed: bool
    reason: str
    evaluated_at: datetime


class ResponseActionResponse(BaseModel):
    """Detailed response action representation."""

    id: UUID
    incident_id: UUID
    action_type: ActionType
    target: str
    status: ActionStatus
    idempotency_key: str
    parameters: dict[str, Any]
    guardrail_decisions: list[GuardrailDecisionSchema]
    ttl_seconds: int | None = None
    expires_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    executed_at: datetime | None = None
    rolled_back_at: datetime | None = None
    approved_by: str | None = None
    denial_reason: str | None = None
    rollback_reason: str | None = None
    execution_result: dict[str, Any]


class ActionApprovalRequest(BaseModel):
    """Payload to approve a pending response action."""

    notes: str | None = None


class ActionDenialRequest(BaseModel):
    """Payload to deny a pending response action."""

    reason: str = Field(..., min_length=3, max_length=500)


class ActionRollbackRequest(BaseModel):
    """Payload to revert a previously executed response action."""

    reason: str = Field(..., min_length=3, max_length=500)


class ActionDryRunRequest(BaseModel):
    """Payload to simulate an action."""

    action_type: ActionType
    target: str
