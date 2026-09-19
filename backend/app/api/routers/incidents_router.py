"""API router for Incidents, Timelines, Notes, and State Transitions."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import require_analyst, require_viewer
from app.api.schemas.common_schemas import PaginatedResponse
from app.api.schemas.incident_schemas import (
    FactorContributionSchema,
    IncidentDetailResponse,
    IncidentNoteRequest,
    IncidentSummaryResponse,
    IncidentTransitionRequest,
    RiskBreakdownSchema,
    TimelineEntryResponse,
)
from app.db.session import get_db_session
from app.domain.enums import IncidentPriority, IncidentStatus
from app.domain.exceptions import InvalidStateTransitionError
from app.domain.user import User
from app.repositories.incident_repository import IncidentRepository
from app.services.incident_lifecycle_service import IncidentLifecycleService

router = APIRouter(prefix="/incidents", tags=["Incidents"])


@router.get("", response_model=PaginatedResponse[IncidentSummaryResponse])
@router.get("/", response_model=PaginatedResponse[IncidentSummaryResponse], include_in_schema=False)
async def list_incidents(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[User, Depends(require_viewer)],
    status_filter: IncidentStatus | None = Query(None, alias="status"),
    priority_filter: IncidentPriority | None = Query(None, alias="priority"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> PaginatedResponse[IncidentSummaryResponse]:
    """List incidents with priority and status filters (Viewer role)."""
    repo = IncidentRepository(session)
    incidents, total = await repo.list_incidents(
        status=status_filter,
        priority=priority_filter,
        limit=limit,
        offset=offset,
    )
    items = [
        IncidentSummaryResponse(
            id=inc.id,
            reference_id=inc.reference_id,
            title=inc.title,
            description=inc.description,
            status=inc.status,
            priority=inc.priority,
            risk_score=inc.risk_score,
            primary_src_ip=inc.primary_src_ip,
            primary_host=inc.primary_host,
            primary_username=inc.primary_username,
            created_at=inc.created_at,
            updated_at=inc.updated_at,
            assigned_to=inc.assigned_to,
        )
        for inc in incidents
    ]
    return PaginatedResponse(items=items, total=total, limit=limit, offset=offset)


@router.get("/{incident_id}", response_model=IncidentDetailResponse)
async def get_incident(
    incident_id: UUID,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[User, Depends(require_viewer)],
) -> IncidentDetailResponse:
    """Get full incident details with explainable factor breakdown (Viewer role)."""
    repo = IncidentRepository(session)
    inc = await repo.get_by_id(incident_id)
    if not inc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "INCIDENT_NOT_FOUND",
                    "message": f"Incident '{incident_id}' not found",
                }
            },
        )

    breakdown = RiskBreakdownSchema(
        score=inc.risk_breakdown.score,
        priority=inc.risk_breakdown.priority,
        correlation_bonus=inc.risk_breakdown.correlation_bonus,
        summary=inc.risk_breakdown.summary,
        factors=[
            FactorContributionSchema(
                factor_name=f.factor_name,
                raw_value=f.raw_value,
                weight=f.weight,
                contribution=f.contribution,
                explanation=f.explanation,
            )
            for f in inc.risk_breakdown.factors
        ],
    )

    return IncidentDetailResponse(
        id=inc.id,
        reference_id=inc.reference_id,
        title=inc.title,
        description=inc.description,
        status=inc.status,
        priority=inc.priority,
        risk_score=inc.risk_score,
        risk_breakdown=breakdown,
        primary_src_ip=inc.primary_src_ip,
        primary_host=inc.primary_host,
        primary_username=inc.primary_username,
        mitre_tactics=inc.mitre_tactics,
        mitre_techniques=inc.mitre_techniques,
        affected_asset_ids=inc.affected_asset_ids,
        created_at=inc.created_at,
        updated_at=inc.updated_at,
        assigned_to=inc.assigned_to,
        closed_at=inc.closed_at,
        close_notes=inc.close_notes,
    )


@router.get("/{incident_id}/timeline", response_model=list[TimelineEntryResponse])
async def get_incident_timeline(
    incident_id: UUID,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[User, Depends(require_viewer)],
) -> list[TimelineEntryResponse]:
    """Retrieve full chronological investigation timeline (Viewer role)."""
    repo = IncidentRepository(session)
    entries = await repo.list_timeline(incident_id)
    return [
        TimelineEntryResponse(
            id=e.id,
            incident_id=e.incident_id,
            timestamp=e.timestamp,
            entry_type=e.entry_type,
            title=e.title,
            description=e.description,
            actor=e.actor,
            mitre_tactic=e.mitre_tactic,
            mitre_technique=e.mitre_technique,
            metadata=e.metadata,
        )
        for e in entries
    ]


@router.post("/{incident_id}/transition", response_model=IncidentDetailResponse)
async def transition_incident_state(
    incident_id: UUID,
    payload: IncidentTransitionRequest,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_analyst)],
) -> IncidentDetailResponse:
    """Perform a manual incident lifecycle transition (Analyst role required)."""
    lifecycle_service = IncidentLifecycleService(session)
    try:
        await lifecycle_service.transition_incident(
            incident_id=incident_id,
            target_status=payload.target_status,
            user_role=current_user.role,
            actor_username=current_user.username,
            notes=payload.notes,
        )
    except InvalidStateTransitionError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {"code": "INVALID_STATE_TRANSITION", "message": err.message}},
        ) from err

    return await get_incident(incident_id, session, current_user)


@router.post(
    "/{incident_id}/notes",
    response_model=TimelineEntryResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_incident_note(
    incident_id: UUID,
    payload: IncidentNoteRequest,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_analyst)],
) -> TimelineEntryResponse:
    """Add an analyst note to the incident timeline and hash ledger (Analyst role required)."""
    lifecycle_service = IncidentLifecycleService(session)
    entry = await lifecycle_service.add_analyst_note(
        incident_id=incident_id,
        note=payload.note,
        actor_username=current_user.username,
    )
    return TimelineEntryResponse(
        id=entry.id,
        incident_id=entry.incident_id,
        timestamp=entry.timestamp,
        entry_type=entry.entry_type,
        title=entry.title,
        description=entry.description,
        actor=entry.actor,
        mitre_tactic=entry.mitre_tactic,
        mitre_technique=entry.mitre_technique,
        metadata=entry.metadata,
    )
