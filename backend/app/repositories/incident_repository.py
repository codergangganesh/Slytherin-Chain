"""Repository for Incident, Timeline, and correlated Alert data access."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.orm_models import AlertOrm, IncidentAlertOrm, IncidentOrm, TimelineEntryOrm
from app.domain.enums import IncidentPriority, IncidentStatus
from app.domain.incident import Incident, TimelineEntry
from app.domain.risk_score import RiskFactorContribution, RiskScoreResult


class IncidentRepository:
    """Encapsulates all database operations for Incident entities."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @staticmethod
    def _to_domain(orm: IncidentOrm) -> Incident:
        """Convert IncidentOrm to domain Incident."""
        risk_raw = orm.risk_breakdown or {}
        factors = [
            RiskFactorContribution(
                factor_name=f.get("factor_name", ""),
                raw_value=float(f.get("raw_value", 0.0)),
                weight=float(f.get("weight", 0.0)),
                contribution=float(f.get("contribution", 0.0)),
                explanation=f.get("explanation", ""),
            )
            for f in risk_raw.get("factors", [])
        ]
        risk_result = RiskScoreResult(
            score=orm.risk_score,
            priority=IncidentPriority(orm.priority),
            factors=factors,
            correlation_bonus=float(risk_raw.get("correlation_bonus", 0.0)),
            summary=risk_raw.get("summary", ""),
        )

        return Incident(
            id=orm.id,
            reference_id=orm.reference_id,
            title=orm.title,
            description=orm.description,
            status=IncidentStatus(orm.status),
            priority=IncidentPriority(orm.priority),
            risk_score=orm.risk_score,
            risk_breakdown=risk_result,
            primary_src_ip=orm.primary_src_ip,
            primary_host=orm.primary_host,
            primary_username=orm.primary_username,
            created_at=orm.created_at,
            updated_at=orm.updated_at,
            assigned_to=orm.assigned_to,
            mitre_tactics=list(orm.mitre_tactics) if orm.mitre_tactics else [],
            mitre_techniques=list(orm.mitre_techniques) if orm.mitre_techniques else [],
            affected_asset_ids=[UUID(str(aid)) for aid in (orm.affected_asset_ids or [])],
            closed_at=orm.closed_at,
            close_notes=orm.close_notes,
        )

    @staticmethod
    def _to_timeline_domain(orm: TimelineEntryOrm) -> TimelineEntry:
        """Convert TimelineEntryOrm to domain TimelineEntry."""
        return TimelineEntry(
            id=orm.id,
            incident_id=orm.incident_id,
            timestamp=orm.timestamp,
            entry_type=orm.entry_type,
            title=orm.title,
            description=orm.description,
            actor=orm.actor,
            mitre_tactic=orm.mitre_tactic,
            mitre_technique=orm.mitre_technique,
            metadata=orm.extra_metadata or {},
        )

    async def generate_reference_id(self) -> str:
        """Generate a consecutive reference ID like INC-2026-0001."""
        year = datetime.now(UTC).year
        count_stmt = select(func.count()).select_from(IncidentOrm)
        count = await self._session.scalar(count_stmt) or 0
        return f"INC-{year}-{count + 1:04d}"

    async def create(
        self,
        title: str,
        description: str,
        status: IncidentStatus,
        priority: IncidentPriority,
        risk_score: float,
        risk_breakdown: dict[str, Any],
        primary_src_ip: str | None = None,
        primary_host: str | None = None,
        primary_username: str | None = None,
        mitre_tactics: list[str] | None = None,
        mitre_techniques: list[str] | None = None,
        affected_asset_ids: list[str] | None = None,
    ) -> Incident:
        """Create and persist a new incident."""
        ref_id = await self.generate_reference_id()
        orm = IncidentOrm(
            reference_id=ref_id,
            title=title,
            description=description,
            status=status,
            priority=priority,
            risk_score=risk_score,
            risk_breakdown=risk_breakdown,
            primary_src_ip=primary_src_ip,
            primary_host=primary_host,
            primary_username=primary_username,
            mitre_tactics=mitre_tactics or [],
            mitre_techniques=mitre_techniques or [],
            affected_asset_ids=affected_asset_ids or [],
        )
        self._session.add(orm)
        await self._session.flush()
        await self._session.refresh(orm)
        return self._to_domain(orm)

    async def get_by_id(self, incident_id: UUID) -> Incident | None:
        """Find an incident by UUID."""
        stmt = select(IncidentOrm).where(IncidentOrm.id == incident_id)
        result = await self._session.execute(stmt)
        orm = result.scalar_one_or_none()
        return self._to_domain(orm) if orm else None

    async def find_open_incident_by_correlation_key(
        self,
        src_ip: str | None,
        host: str | None,
        username: str | None,
        correlation_cutoff: datetime,
    ) -> Incident | None:
        """Find an open incident matching any of the primary keys within the window."""
        stmt = select(IncidentOrm).where(
            IncidentOrm.status.notin_(
                [IncidentStatus.RESOLVED, IncidentStatus.CLOSED, IncidentStatus.FALSE_POSITIVE]
            ),
            IncidentOrm.created_at >= correlation_cutoff,
        )
        if src_ip:
            stmt = stmt.where(IncidentOrm.primary_src_ip == src_ip)
        elif host:
            stmt = stmt.where(IncidentOrm.primary_host == host)
        elif username:
            stmt = stmt.where(IncidentOrm.primary_username == username)
        else:
            return None

        result = await self._session.execute(stmt.order_by(IncidentOrm.created_at.desc()))
        orm = result.scalars().first()
        return self._to_domain(orm) if orm else None

    async def update_incident(
        self,
        incident_id: UUID,
        status: IncidentStatus | None = None,
        priority: IncidentPriority | None = None,
        risk_score: float | None = None,
        risk_breakdown: dict[str, Any] | None = None,
        assigned_to: str | None = None,
        mitre_tactics: list[str] | None = None,
        mitre_techniques: list[str] | None = None,
        closed_at: datetime | None = None,
        close_notes: str | None = None,
    ) -> Incident | None:
        """Update fields of an existing incident."""
        stmt = select(IncidentOrm).where(IncidentOrm.id == incident_id)
        result = await self._session.execute(stmt)
        orm = result.scalar_one_or_none()
        if not orm:
            return None

        if status is not None:
            orm.status = status
        if priority is not None:
            orm.priority = priority
        if risk_score is not None:
            orm.risk_score = risk_score
        if risk_breakdown is not None:
            orm.risk_breakdown = risk_breakdown
        if assigned_to is not None:
            orm.assigned_to = assigned_to
        if mitre_tactics is not None:
            orm.mitre_tactics = mitre_tactics
        if mitre_techniques is not None:
            orm.mitre_techniques = mitre_techniques
        if closed_at is not None:
            orm.closed_at = closed_at
        if close_notes is not None:
            orm.close_notes = close_notes

        await self._session.flush()
        await self._session.refresh(orm)
        return self._to_domain(orm)

    async def list_incidents(
        self,
        status: IncidentStatus | None = None,
        priority: IncidentPriority | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[Incident], int]:
        """List incidents ordered by priority and risk score descending."""
        stmt = select(IncidentOrm)
        count_stmt = select(func.count()).select_from(IncidentOrm)

        if status:
            stmt = stmt.where(IncidentOrm.status == status)
            count_stmt = count_stmt.where(IncidentOrm.status == status)
        if priority:
            stmt = stmt.where(IncidentOrm.priority == priority)
            count_stmt = count_stmt.where(IncidentOrm.priority == priority)

        total = await self._session.scalar(count_stmt) or 0
        result = await self._session.execute(
            stmt.order_by(IncidentOrm.risk_score.desc(), IncidentOrm.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        incidents = [self._to_domain(orm) for orm in result.scalars().all()]
        return incidents, total

    async def add_timeline_entry(
        self,
        incident_id: UUID,
        entry_type: str,
        title: str,
        description: str,
        actor: str = "system",
        mitre_tactic: str | None = None,
        mitre_technique: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> TimelineEntry:
        """Append a timeline entry to an incident."""
        orm = TimelineEntryOrm(
            incident_id=incident_id,
            entry_type=entry_type,
            title=title,
            description=description,
            actor=actor,
            mitre_tactic=mitre_tactic,
            mitre_technique=mitre_technique,
            extra_metadata=metadata or {},
        )
        self._session.add(orm)
        await self._session.flush()
        await self._session.refresh(orm)
        return self._to_timeline_domain(orm)

    async def list_timeline(self, incident_id: UUID) -> list[TimelineEntry]:
        """Retrieve the chronological timeline for an incident."""
        stmt = (
            select(TimelineEntryOrm)
            .where(TimelineEntryOrm.incident_id == incident_id)
            .order_by(TimelineEntryOrm.timestamp.asc())
        )
        result = await self._session.execute(stmt)
        return [self._to_timeline_domain(orm) for orm in result.scalars().all()]

    async def link_alert(self, incident_id: UUID, alert_id: UUID) -> None:
        """Link an alert to an incident."""
        link = IncidentAlertOrm(incident_id=incident_id, alert_id=alert_id)
        self._session.add(link)
        # Also update alert table incident_id
        stmt = select(AlertOrm).where(AlertOrm.id == alert_id)
        res = await self._session.execute(stmt)
        alert_orm = res.scalar_one_or_none()
        if alert_orm:
            alert_orm.incident_id = incident_id
        await self._session.flush()
