"""API router for Response Actions, Approvals, Denials, Rollbacks, and Dry-runs."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import require_analyst, require_viewer
from app.api.schemas.common_schemas import PaginatedResponse
from app.api.schemas.response_action_schemas import (
    ActionApprovalRequest,
    ActionDenialRequest,
    ActionDryRunRequest,
    ActionRollbackRequest,
    GuardrailDecisionSchema,
    ResponseActionResponse,
)
from app.db.session import get_db_session
from app.domain.enums import ActionStatus, ActionType
from app.domain.exceptions import EntityNotFoundError
from app.domain.response_action import ResponseAction
from app.domain.user import User
from app.repositories.response_action_repository import ResponseActionRepository
from app.services.response.response_orchestrator import ResponseOrchestrator

router = APIRouter(prefix="/response-actions", tags=["Response Actions"])


def _to_response_schema(a: ResponseAction) -> ResponseActionResponse:
    """Format domain ResponseAction to Pydantic response."""
    return ResponseActionResponse(
        id=a.id,
        incident_id=a.incident_id,
        action_type=a.action_type,
        target=a.target,
        status=a.status,
        idempotency_key=a.idempotency_key,
        parameters=a.parameters,
        guardrail_decisions=[
            GuardrailDecisionSchema(
                guardrail_name=d.guardrail_name,
                passed=d.passed,
                reason=d.reason,
                evaluated_at=d.evaluated_at,
            )
            for d in a.guardrail_decisions
        ],
        ttl_seconds=a.ttl_seconds,
        expires_at=a.expires_at,
        created_at=a.created_at,
        updated_at=a.updated_at,
        executed_at=a.executed_at,
        rolled_back_at=a.rolled_back_at,
        approved_by=a.approved_by,
        denial_reason=a.denial_reason,
        rollback_reason=a.rollback_reason,
        execution_result=a.execution_result,
    )


@router.get("", response_model=PaginatedResponse[ResponseActionResponse])
@router.get("/", response_model=PaginatedResponse[ResponseActionResponse], include_in_schema=False)
async def list_response_actions(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[User, Depends(require_viewer)],
    incident_id: UUID | None = Query(None),
    status_filter: ActionStatus | None = Query(None, alias="status"),
    action_type: ActionType | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> PaginatedResponse[ResponseActionResponse]:
    """List response actions with status and incident filters (Viewer role)."""
    repo = ResponseActionRepository(session)
    actions, total = await repo.list_actions(
        incident_id=incident_id,
        status=status_filter,
        action_type=action_type,
        limit=limit,
        offset=offset,
    )
    items = [_to_response_schema(a) for a in actions]
    return PaginatedResponse(items=items, total=total, limit=limit, offset=offset)


@router.post("/{action_id}/approve", response_model=ResponseActionResponse)
async def approve_response_action(
    action_id: UUID,
    payload: ActionApprovalRequest,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_analyst)],
) -> ResponseActionResponse:
    """Manually approve and execute a pending response action (Analyst role)."""
    orchestrator = ResponseOrchestrator(session)
    try:
        updated = await orchestrator.approve_action(action_id, current_user.username)
        return _to_response_schema(updated)
    except EntityNotFoundError as err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "ACTION_NOT_FOUND", "message": err.message}},
        ) from err


@router.post("/{action_id}/deny", response_model=ResponseActionResponse)
async def deny_response_action(
    action_id: UUID,
    payload: ActionDenialRequest,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_analyst)],
) -> ResponseActionResponse:
    """Manually deny a pending response action (Analyst role)."""
    orchestrator = ResponseOrchestrator(session)
    try:
        updated = await orchestrator.deny_action(action_id, current_user.username, payload.reason)
        return _to_response_schema(updated)
    except EntityNotFoundError as err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "ACTION_NOT_FOUND", "message": err.message}},
        ) from err


@router.post("/{action_id}/rollback", response_model=ResponseActionResponse)
async def rollback_response_action(
    action_id: UUID,
    payload: ActionRollbackRequest,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_analyst)],
) -> ResponseActionResponse:
    """Revert a previously executed response action with reason (Analyst role)."""
    orchestrator = ResponseOrchestrator(session)
    try:
        updated = await orchestrator.rollback_action(
            action_id, current_user.username, payload.reason
        )
        return _to_response_schema(updated)
    except EntityNotFoundError as err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "ACTION_NOT_FOUND", "message": err.message}},
        ) from err


@router.post("/dry-run")
async def dry_run_action(
    payload: ActionDryRunRequest,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[User, Depends(require_analyst)],
) -> dict[str, str | int | float | bool | dict[str, str]]:
    """Simulate an action execution and return anticipated effects without mutating state."""
    orchestrator = ResponseOrchestrator(session)
    result = await orchestrator.dry_run_action(payload.action_type, payload.target)
    return result
