"""Repository for Ingested Normalized Events."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.orm_models import EventOrm
from app.domain.enums import EventSource, EventType
from app.domain.normalized_event import NormalizedEvent


class EventRepository:
    """Encapsulates all database operations for security events."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @staticmethod
    def _to_domain(orm: EventOrm) -> NormalizedEvent:
        """Convert ORM model to domain NormalizedEvent."""
        return NormalizedEvent(
            event_id=orm.event_id,
            occurred_at=orm.occurred_at,
            ingested_at=orm.ingested_at,
            source=EventSource(orm.source),
            event_type=EventType(orm.event_type),
            host=orm.host,
            username=orm.username,
            src_ip=orm.src_ip,
            dst_ip=orm.dst_ip,
            dst_port=orm.dst_port,
            process_name=orm.process_name,
            command_line=orm.command_line,
            file_path=orm.file_path,
            file_hash_sha256=orm.file_hash_sha256,
            bytes_out=orm.bytes_out,
            http_path=orm.http_path,
            severity_hint=orm.severity_hint,
            raw=orm.raw or {},
        )

    async def save(self, event: NormalizedEvent) -> NormalizedEvent:
        """Save a single normalized event."""
        orm = EventOrm(
            event_id=event.event_id,
            occurred_at=event.occurred_at,
            ingested_at=event.ingested_at,
            source=event.source,
            event_type=event.event_type,
            host=event.host,
            username=event.username,
            src_ip=event.src_ip,
            dst_ip=event.dst_ip,
            dst_port=event.dst_port,
            process_name=event.process_name,
            command_line=event.command_line,
            file_path=event.file_path,
            file_hash_sha256=event.file_hash_sha256,
            bytes_out=event.bytes_out,
            http_path=event.http_path,
            severity_hint=event.severity_hint,
            raw=event.raw,
        )
        self._session.add(orm)
        await self._session.flush()
        return event

    async def save_batch(self, events: list[NormalizedEvent]) -> list[NormalizedEvent]:
        """Save a batch of normalized events efficiently."""
        orms = [
            EventOrm(
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
        self._session.add_all(orms)
        await self._session.flush()
        return events

    async def get_by_id(self, event_id: UUID) -> NormalizedEvent | None:
        """Find an event by UUID."""
        stmt = select(EventOrm).where(EventOrm.event_id == event_id)
        result = await self._session.execute(stmt)
        orm = result.scalar_one_or_none()
        return self._to_domain(orm) if orm else None

    async def list_events(
        self,
        src_ip: str | None = None,
        host: str | None = None,
        username: str | None = None,
        event_type: EventType | None = None,
        source: EventSource | None = None,
        from_time: datetime | None = None,
        to_time: datetime | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[NormalizedEvent], int]:
        """List events with filtering and count."""
        stmt = select(EventOrm)
        count_stmt = select(func.count()).select_from(EventOrm)

        if src_ip:
            stmt = stmt.where(EventOrm.src_ip == src_ip)
            count_stmt = count_stmt.where(EventOrm.src_ip == src_ip)
        if host:
            stmt = stmt.where(EventOrm.host == host)
            count_stmt = count_stmt.where(EventOrm.host == host)
        if username:
            stmt = stmt.where(EventOrm.username == username)
            count_stmt = count_stmt.where(EventOrm.username == username)
        if event_type:
            stmt = stmt.where(EventOrm.event_type == event_type)
            count_stmt = count_stmt.where(EventOrm.event_type == event_type)
        if source:
            stmt = stmt.where(EventOrm.source == source)
            count_stmt = count_stmt.where(EventOrm.source == source)
        if from_time:
            stmt = stmt.where(EventOrm.occurred_at >= from_time)
            count_stmt = count_stmt.where(EventOrm.occurred_at >= from_time)
        if to_time:
            stmt = stmt.where(EventOrm.occurred_at <= to_time)
            count_stmt = count_stmt.where(EventOrm.occurred_at <= to_time)

        total = await self._session.scalar(count_stmt) or 0
        result = await self._session.execute(
            stmt.order_by(EventOrm.occurred_at.desc()).limit(limit).offset(offset)
        )
        events = [self._to_domain(orm) for orm in result.scalars().all()]
        return events, total
