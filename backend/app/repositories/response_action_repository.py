"""Repository for Response Actions and enforcement history."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.orm_models import ResponseActionOrm
from app.domain.enums import ActionStatus, ActionType
from app.domain.response_action import GuardrailDecision, ResponseAction


class ResponseActionRepository:
    """Encapsulates database operations for response actions."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @staticmethod
    def _to_domain(orm: ResponseActionOrm) -> ResponseAction:
        """Convert ORM model to domain ResponseAction."""
        decisions = [
            GuardrailDecision(
                guardrail_name=d.get("guardrail_name", ""),
                passed=bool(d.get("passed", False)),
                reason=d.get("reason", ""),
                evaluated_at=datetime.fromisoformat(
                    d.get("evaluated_at", datetime.now(UTC).isoformat())
                ),
            )
            for d in (orm.guardrail_decisions or [])
        ]

        return ResponseAction(
            id=orm.id,
            incident_id=orm.incident_id,
            action_type=ActionType(orm.action_type),
            target=orm.target,
            status=ActionStatus(orm.status),
            idempotency_key=orm.idempotency_key,
            parameters=orm.parameters or {},
            guardrail_decisions=decisions,
            created_at=orm.created_at,
            updated_at=orm.updated_at,
            ttl_seconds=orm.ttl_seconds,
            expires_at=orm.expires_at,
            executed_at=orm.executed_at,
            rolled_back_at=orm.rolled_back_at,
            approved_by=orm.approved_by,
            denial_reason=orm.denial_reason,
            rollback_reason=orm.rollback_reason,
            execution_result=orm.execution_result or {},
            retry_count=orm.retry_count,
        )

    async def get_by_id(self, action_id: UUID) -> ResponseAction | None:
        """Find action by UUID."""
        stmt = select(ResponseActionOrm).where(ResponseActionOrm.id == action_id)
        result = await self._session.execute(stmt)
        orm = result.scalar_one_or_none()
        return self._to_domain(orm) if orm else None

    async def get_by_idempotency_key(self, idempotency_key: str) -> ResponseAction | None:
        """Find action by idempotency key."""
        stmt = select(ResponseActionOrm).where(ResponseActionOrm.idempotency_key == idempotency_key)
        result = await self._session.execute(stmt)
        orm = result.scalar_one_or_none()
        return self._to_domain(orm) if orm else None

    async def create(
        self,
        incident_id: UUID,
        action_type: ActionType,
        target: str,
        idempotency_key: str,
        parameters: dict[str, Any],
        guardrail_decisions: list[dict[str, Any]],
        status: ActionStatus = ActionStatus.PROPOSED,
        ttl_seconds: int | None = None,
        denial_reason: str | None = None,
    ) -> ResponseAction:
        """Create and persist a response action."""
        now = datetime.now(UTC)
        expires_at = now + timedelta(seconds=ttl_seconds) if ttl_seconds else None

        orm = ResponseActionOrm(
            incident_id=incident_id,
            action_type=action_type,
            target=target,
            status=status,
            idempotency_key=idempotency_key,
            parameters=parameters,
            guardrail_decisions=guardrail_decisions,
            ttl_seconds=ttl_seconds,
            expires_at=expires_at,
            created_at=now,
            updated_at=now,
            denial_reason=denial_reason,
        )
        self._session.add(orm)
        await self._session.flush()
        await self._session.refresh(orm)
        return self._to_domain(orm)

    async def update_status(
        self,
        action_id: UUID,
        status: ActionStatus,
        executed_at: datetime | None = None,
        rolled_back_at: datetime | None = None,
        approved_by: str | None = None,
        denial_reason: str | None = None,
        rollback_reason: str | None = None,
        execution_result: dict[str, Any] | None = None,
    ) -> ResponseAction | None:
        """Update the lifecycle status and execution outcomes of an action."""
        stmt = select(ResponseActionOrm).where(ResponseActionOrm.id == action_id)
        result = await self._session.execute(stmt)
        orm = result.scalar_one_or_none()
        if not orm:
            return None

        orm.status = status
        if executed_at is not None:
            orm.executed_at = executed_at
        if rolled_back_at is not None:
            orm.rolled_back_at = rolled_back_at
        if approved_by is not None:
            orm.approved_by = approved_by
        if denial_reason is not None:
            orm.denial_reason = denial_reason
        if rollback_reason is not None:
            orm.rollback_reason = rollback_reason
        if execution_result is not None:
            orm.execution_result = execution_result

        await self._session.flush()
        await self._session.refresh(orm)
        return self._to_domain(orm)

    async def count_actions_in_window(self, hours: int = 1, target_type: str | None = None) -> int:
        """Count executed actions in the last N hours for blast radius checking."""
        cutoff = datetime.now(UTC) - timedelta(hours=hours)
        stmt = (
            select(func.count())
            .select_from(ResponseActionOrm)
            .where(
                ResponseActionOrm.status.in_([ActionStatus.SUCCEEDED, ActionStatus.EXECUTING]),
                ResponseActionOrm.created_at >= cutoff,
            )
        )
        if target_type:
            stmt = stmt.where(ResponseActionOrm.action_type == target_type)

        count = await self._session.scalar(stmt) or 0
        return count

    async def list_actions(
        self,
        incident_id: UUID | None = None,
        status: ActionStatus | None = None,
        action_type: ActionType | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[ResponseAction], int]:
        """List response actions with filtering."""
        stmt = select(ResponseActionOrm)
        count_stmt = select(func.count()).select_from(ResponseActionOrm)

        if incident_id:
            stmt = stmt.where(ResponseActionOrm.incident_id == incident_id)
            count_stmt = count_stmt.where(ResponseActionOrm.incident_id == incident_id)
        if status:
            stmt = stmt.where(ResponseActionOrm.status == status)
            count_stmt = count_stmt.where(ResponseActionOrm.status == status)
        if action_type:
            stmt = stmt.where(ResponseActionOrm.action_type == action_type)
            count_stmt = count_stmt.where(ResponseActionOrm.action_type == action_type)

        total = await self._session.scalar(count_stmt) or 0
        result = await self._session.execute(
            stmt.order_by(ResponseActionOrm.created_at.desc()).limit(limit).offset(offset)
        )
        return [self._to_domain(orm) for orm in result.scalars().all()], total

    async def list_expired_actions(self) -> list[ResponseAction]:
        """List active actions whose TTL has expired."""
        now = datetime.now(UTC)
        stmt = (
            select(ResponseActionOrm)
            .where(
                ResponseActionOrm.status == ActionStatus.SUCCEEDED,
                ResponseActionOrm.expires_at.is_not(None),
                ResponseActionOrm.expires_at <= now,
            )
            .order_by(ResponseActionOrm.expires_at.asc())
        )
        result = await self._session.execute(stmt)
        return [self._to_domain(orm) for orm in result.scalars().all()]
