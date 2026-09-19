"""Domain model for Incidents and Timeline entries."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID

from app.domain.enums import IncidentPriority, IncidentStatus
from app.domain.risk_score import RiskScoreResult


@dataclass(frozen=True)
class TimelineEntry:
    """Represents a discrete chronological event in the incident investigation history."""

    id: UUID
    incident_id: UUID
    timestamp: datetime
    entry_type: str
    title: str
    description: str
    actor: str  # e.g., "system", "analyst:alice"
    mitre_tactic: str | None = None
    mitre_technique: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Incident:
    """Represents a prioritized security incident correlated across alerts."""

    id: UUID
    reference_id: str  # Format: INC-YYYY-NNNN
    title: str
    description: str
    status: IncidentStatus
    priority: IncidentPriority
    risk_score: float
    risk_breakdown: RiskScoreResult
    primary_src_ip: str | None
    primary_host: str | None
    primary_username: str | None
    created_at: datetime
    updated_at: datetime
    assigned_to: str | None = None
    mitre_tactics: list[str] = field(default_factory=list)
    mitre_techniques: list[str] = field(default_factory=list)
    affected_asset_ids: list[UUID] = field(default_factory=list)
    closed_at: datetime | None = None
    close_notes: str | None = None
