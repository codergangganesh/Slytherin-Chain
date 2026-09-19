"""Incident request and response schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID
from pydantic import BaseModel, Field

from app.domain.enums import IncidentPriority, IncidentStatus


class FactorContributionSchema(BaseModel):
    """Schema for individual risk score factor."""

    factor_name: str
    raw_value: float
    weight: float
    contribution: float
    explanation: str


class RiskBreakdownSchema(BaseModel):
    """Schema for complete risk scoring breakdown."""

    score: float
    priority: IncidentPriority
    correlation_bonus: float
    summary: str
    factors: list[FactorContributionSchema] = Field(default_factory=list)


class IncidentSummaryResponse(BaseModel):
    """Compact incident representation for queues."""

    id: UUID
    reference_id: str
    title: str
    description: str
    status: IncidentStatus
    priority: IncidentPriority
    risk_score: float
    primary_src_ip: str | None
    primary_host: str | None
    primary_username: str | None
    created_at: datetime
    updated_at: datetime
    assigned_to: str | None = None


class IncidentDetailResponse(IncidentSummaryResponse):
    """Full incident details including factor breakdown and MITRE mappings."""

    risk_breakdown: RiskBreakdownSchema
    mitre_tactics: list[str]
    mitre_techniques: list[str]
    affected_asset_ids: list[UUID]
    closed_at: datetime | None = None
    close_notes: str | None = None


class TimelineEntryResponse(BaseModel):
    """Incident timeline item representation."""

    id: UUID
    incident_id: UUID
    timestamp: datetime
    entry_type: str
    title: str
    description: str
    actor: str
    mitre_tactic: str | None = None
    mitre_technique: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class IncidentTransitionRequest(BaseModel):
    """Payload to request an incident state transition."""

    target_status: IncidentStatus
    notes: str | None = Field(default=None, description="Mandatory for closing or false positive")


class IncidentNoteRequest(BaseModel):
    """Payload to add an investigation note."""

    note: str = Field(..., min_length=1, max_length=2000)
