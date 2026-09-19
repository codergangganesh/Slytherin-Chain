"""Repository for Alert persistence and query operations."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.orm_models import AlertOrm
from app.domain.alert import Alert, MitreAttackMapping


class AlertRepository:
    """Encapsulates all database operations for detection alerts."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @staticmethod
    def _to_domain(orm: AlertOrm) -> Alert:
        """Convert ORM model to domain Alert."""
        return Alert(
            id=orm.id,
            rule_id=orm.rule_id,
            title=orm.title,
            description=orm.description,
            severity=orm.severity,
            confidence=orm.confidence,
            mitre=MitreAttackMapping(
                tactic=orm.mitre_tactic,
                technique_id=orm.mitre_technique_id,
                technique_name=orm.mitre_technique_name,
            ),
            playbook_category=orm.playbook_category,
            matched_event_ids=[UUID(str(eid)) for eid in orm.matched_event_ids],
            group_by_key=orm.group_by_key,
            created_at=orm.created_at,
            incident_id=orm.incident_id,
            extra_context=orm.extra_context or {},
        )

    async def save(self, alert: Alert) -> Alert:
        """Persist a newly generated alert."""
        orm = AlertOrm(
            id=alert.id,
            rule_id=alert.rule_id,
            title=alert.title,
            description=alert.description,
            severity=alert.severity,
            confidence=alert.confidence,
            mitre_tactic=alert.mitre.tactic,
            mitre_technique_id=alert.mitre.technique_id,
            mitre_technique_name=alert.mitre.technique_name,
            playbook_category=alert.playbook_category,
            matched_event_ids=[str(eid) for eid in alert.matched_event_ids],
            group_by_key=alert.group_by_key,
            created_at=alert.created_at,
            incident_id=alert.incident_id,
            extra_context=alert.extra_context,
        )
        self._session.add(orm)
        await self._session.flush()
        return alert

    async def is_suppressed(self, rule_id: str, group_by_key: str, suppress_seconds: int) -> bool:
        """Check if an alert for the given rule and group key was raised within the suppression window."""
        cutoff = datetime.now(timezone.utc) - timedelta(seconds=suppress_seconds)
        stmt = (
            select(func.count())
            .select_from(AlertOrm)
            .where(
                AlertOrm.rule_id == rule_id,
                AlertOrm.group_by_key == group_by_key,
                AlertOrm.created_at >= cutoff,
            )
        )
        count = await self._session.scalar(stmt) or 0
        return count > 0

    async def get_by_id(self, alert_id: UUID) -> Alert | None:
        """Find an alert by its ID."""
        stmt = select(AlertOrm).where(AlertOrm.id == alert_id)
        result = await self._session.execute(stmt)
        orm = result.scalar_one_or_none()
        return self._to_domain(orm) if orm else None

    async def list_alerts_by_incident(self, incident_id: UUID) -> list[Alert]:
        """Fetch all alerts correlated to an incident."""
        stmt = select(AlertOrm).where(AlertOrm.incident_id == incident_id).order_by(AlertOrm.created_at.asc())
        result = await self._session.execute(stmt)
        return [self._to_domain(orm) for orm in result.scalars().all()]
