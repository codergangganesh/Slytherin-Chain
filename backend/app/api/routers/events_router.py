"""API router for Security Event Ingestion and Queries."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import require_viewer, verify_ingestion_api_key
from app.api.schemas.common_schemas import PaginatedResponse
from app.api.schemas.event_schemas import (
    BatchEventIngestRequest,
    EventIngestRequest,
    EventResponse,
    IngestResponse,
)
from app.db.session import get_db_session
from app.domain.enums import EventSource, EventType
from app.domain.user import User
from app.repositories.event_repository import EventRepository
from app.services.ingestion.event_normalizer import EventNormalizer
from app.services.ingestion.event_publisher import EventPublisher

router = APIRouter(prefix="/events", tags=["Events"])


@router.post("", response_model=IngestResponse, status_code=status.HTTP_202_ACCEPTED)
@router.post(
    "/",
    response_model=IngestResponse,
    status_code=status.HTTP_202_ACCEPTED,
    include_in_schema=False,
)
async def ingest_single_event(
    payload: EventIngestRequest,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[str, Depends(verify_ingestion_api_key)],
) -> IngestResponse:
    """Ingest a single security event (authenticated via X-API-Key)."""
    normalizer = EventNormalizer()
    normalized = normalizer.normalize(payload.model_dump(exclude_unset=True))

    repo = EventRepository(session)
    await repo.save(normalized)

    publisher = EventPublisher()
    await publisher.publish(normalized)

    return IngestResponse(
        accepted_count=1,
        event_ids=[normalized.event_id],
        status="accepted",
    )


@router.post("/batch", response_model=IngestResponse, status_code=status.HTTP_202_ACCEPTED)
async def ingest_batch_events(
    payload: BatchEventIngestRequest,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[str, Depends(verify_ingestion_api_key)],
) -> IngestResponse:
    """Ingest a batch of up to 500 security events (authenticated via X-API-Key)."""
    normalizer = EventNormalizer()
    normalized_events = [
        normalizer.normalize(item.model_dump(exclude_unset=True)) for item in payload.events
    ]

    repo = EventRepository(session)
    await repo.save_batch(normalized_events)

    publisher = EventPublisher()
    await publisher.publish_batch(normalized_events)

    return IngestResponse(
        accepted_count=len(normalized_events),
        event_ids=[e.event_id for e in normalized_events],
        status="accepted",
    )


@router.get("", response_model=PaginatedResponse[EventResponse])
async def list_events(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[User, Depends(require_viewer)],
    src_ip: str | None = Query(None),
    host: str | None = Query(None),
    username: str | None = Query(None),
    event_type: EventType | None = Query(None),
    source: EventSource | None = Query(None),
    from_time: datetime | None = Query(None),
    to_time: datetime | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> PaginatedResponse[EventResponse]:
    """Query ingested events with filters and pagination (Viewer role required)."""
    repo = EventRepository(session)
    events, total = await repo.list_events(
        src_ip=src_ip,
        host=host,
        username=username,
        event_type=event_type,
        source=source,
        from_time=from_time,
        to_time=to_time,
        limit=limit,
        offset=offset,
    )
    items = [
        EventResponse(
            event_id=e.event_id,
            occurred_at=e.occurred_at,
            ingested_at=e.ingested_at,
            source=e.source,
            event_type=e.event_type,
            host=e.host,
            username=e.username,
            src_ip=e.src_ip,
            dst_ip=e.dst_ip,
            dst_port=e.dst_port,
            process_name=e.process_name,
            command_line=e.command_line,
            file_path=e.file_path,
            file_hash_sha256=e.file_hash_sha256,
            bytes_out=e.bytes_out,
            http_path=e.http_path,
            severity_hint=e.severity_hint,
            raw=e.raw,
        )
        for e in events
    ]
    return PaginatedResponse(items=items, total=total, limit=limit, offset=offset)
