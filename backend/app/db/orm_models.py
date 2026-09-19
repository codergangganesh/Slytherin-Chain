"""SQLAlchemy ORM models for SentinelChain.

Maps all domain tables according to MASTER_PROMPT Section 9.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
import uuid

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    Uuid,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.domain.enums import (
    ActionStatus,
    ActionType,
    AnchorStatus,
    AssetEnvironment,
    EntryType,
    EventSource,
    EventType,
    IncidentPriority,
    IncidentStatus,
    UserRole,
)

# Portable UUID and JSON type mapping
UUID_TYPE = Uuid(as_uuid=True)
JSON_TYPE = JSONB().with_variant(JSON(), "sqlite")


class UserOrm(Base):
    """User accounts table."""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID_TYPE, primary_key=True, default=uuid.uuid4)
    username: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(String(32), nullable=False, default=UserRole.VIEWER)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )


class ApiKeyOrm(Base):
    """Ingestion API keys table."""

    __tablename__ = "api_keys"

    id: Mapped[uuid.UUID] = mapped_column(UUID_TYPE, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    key_hash: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    prefix: Mapped[str] = mapped_column(String(16), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class AssetOrm(Base):
    """Managed IT assets table."""

    __tablename__ = "assets"

    id: Mapped[uuid.UUID] = mapped_column(UUID_TYPE, primary_key=True, default=uuid.uuid4)
    hostname: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, index=True)
    ip_address: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    criticality: Mapped[int] = mapped_column(Integer, nullable=False, default=3)  # 1 - 5
    environment: Mapped[AssetEnvironment] = mapped_column(
        String(32), nullable=False, default=AssetEnvironment.PRODUCTION
    )
    is_protected: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_internet_facing: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    owner: Mapped[str] = mapped_column(String(128), nullable=False, default="Security Ops")
    tags: Mapped[list[str]] = mapped_column(JSON_TYPE, default=list, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )


class EventOrm(Base):
    """Normalized ingested security events table."""

    __tablename__ = "events"

    event_id: Mapped[uuid.UUID] = mapped_column(UUID_TYPE, primary_key=True, default=uuid.uuid4)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    ingested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    source: Mapped[EventSource] = mapped_column(String(32), nullable=False, index=True)
    event_type: Mapped[EventType] = mapped_column(String(64), nullable=False, index=True)
    host: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    username: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    src_ip: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    dst_ip: Mapped[str | None] = mapped_column(String(64), nullable=True)
    dst_port: Mapped[int | None] = mapped_column(Integer, nullable=True)
    process_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    command_line: Mapped[str | None] = mapped_column(Text, nullable=True)
    file_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    file_hash_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    bytes_out: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    http_path: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    severity_hint: Mapped[int | None] = mapped_column(Integer, nullable=True)
    raw: Mapped[dict[str, Any]] = mapped_column(JSON_TYPE, default=dict, nullable=False)

    __table_args__ = (
        Index("ix_events_src_ip_occurred", "src_ip", "occurred_at"),
        Index("ix_events_host_occurred", "host", "occurred_at"),
    )


class AlertOrm(Base):
    """Security detection alerts table."""

    __tablename__ = "alerts"

    id: Mapped[uuid.UUID] = mapped_column(UUID_TYPE, primary_key=True, default=uuid.uuid4)
    rule_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[float] = mapped_column(Float, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    mitre_tactic: Mapped[str] = mapped_column(String(64), nullable=False)
    mitre_technique_id: Mapped[str] = mapped_column(String(32), nullable=False)
    mitre_technique_name: Mapped[str] = mapped_column(String(128), nullable=False)
    playbook_category: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    matched_event_ids: Mapped[list[str]] = mapped_column(JSON_TYPE, default=list, nullable=False)
    group_by_key: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    incident_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID_TYPE, ForeignKey("incidents.id", ondelete="SET NULL"), nullable=True, index=True
    )
    extra_context: Mapped[dict[str, Any]] = mapped_column(JSON_TYPE, default=dict, nullable=False)

    incident: Mapped[IncidentOrm | None] = relationship("IncidentOrm", back_populates="alerts")


class IncidentOrm(Base):
    """Correlated security incidents table."""

    __tablename__ = "incidents"

    id: Mapped[uuid.UUID] = mapped_column(UUID_TYPE, primary_key=True, default=uuid.uuid4)
    reference_id: Mapped[str] = mapped_column(String(32), unique=True, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[IncidentStatus] = mapped_column(
        String(32), nullable=False, default=IncidentStatus.NEW, index=True
    )
    priority: Mapped[IncidentPriority] = mapped_column(
        String(8), nullable=False, default=IncidentPriority.P3, index=True
    )
    risk_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0, index=True)
    risk_breakdown: Mapped[dict[str, Any]] = mapped_column(JSON_TYPE, default=dict, nullable=False)
    primary_src_ip: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    primary_host: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    primary_username: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    assigned_to: Mapped[str | None] = mapped_column(String(64), nullable=True)
    mitre_tactics: Mapped[list[str]] = mapped_column(JSON_TYPE, default=list, nullable=False)
    mitre_techniques: Mapped[list[str]] = mapped_column(JSON_TYPE, default=list, nullable=False)
    affected_asset_ids: Mapped[list[str]] = mapped_column(JSON_TYPE, default=list, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False, index=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    close_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    alerts: Mapped[list[AlertOrm]] = relationship("AlertOrm", back_populates="incident")
    actions: Mapped[list[ResponseActionOrm]] = relationship("ResponseActionOrm", back_populates="incident")
    timeline_entries: Mapped[list[TimelineEntryOrm]] = relationship(
        "TimelineEntryOrm", back_populates="incident", cascade="all, delete-orphan"
    )


class TimelineEntryOrm(Base):
    """Incident timeline entries table."""

    __tablename__ = "incident_timeline"

    id: Mapped[uuid.UUID] = mapped_column(UUID_TYPE, primary_key=True, default=uuid.uuid4)
    incident_id: Mapped[uuid.UUID] = mapped_column(
        UUID_TYPE, ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    entry_type: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    actor: Mapped[str] = mapped_column(String(64), nullable=False, default="system")
    mitre_tactic: Mapped[str | None] = mapped_column(String(64), nullable=True)
    mitre_technique: Mapped[str | None] = mapped_column(String(32), nullable=True)
    extra_metadata: Mapped[dict[str, Any]] = mapped_column(JSON_TYPE, default=dict, nullable=False)

    incident: Mapped[IncidentOrm] = relationship("IncidentOrm", back_populates="timeline_entries")


class IncidentAlertOrm(Base):
    """Many-to-many link between incidents and alerts."""

    __tablename__ = "incident_alerts"

    incident_id: Mapped[uuid.UUID] = mapped_column(
        UUID_TYPE, ForeignKey("incidents.id", ondelete="CASCADE"), primary_key=True
    )
    alert_id: Mapped[uuid.UUID] = mapped_column(
        UUID_TYPE, ForeignKey("alerts.id", ondelete="CASCADE"), primary_key=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)


class ResponseActionOrm(Base):
    """Autonomous and approved response actions table."""

    __tablename__ = "response_actions"

    id: Mapped[uuid.UUID] = mapped_column(UUID_TYPE, primary_key=True, default=uuid.uuid4)
    incident_id: Mapped[uuid.UUID] = mapped_column(
        UUID_TYPE, ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    action_type: Mapped[ActionType] = mapped_column(String(32), nullable=False, index=True)
    target: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    status: Mapped[ActionStatus] = mapped_column(
        String(32), nullable=False, default=ActionStatus.PROPOSED, index=True
    )
    idempotency_key: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    parameters: Mapped[dict[str, Any]] = mapped_column(JSON_TYPE, default=dict, nullable=False)
    guardrail_decisions: Mapped[list[dict[str, Any]]] = mapped_column(JSON_TYPE, default=list, nullable=False)
    ttl_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
    executed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    rolled_back_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    approved_by: Mapped[str | None] = mapped_column(String(64), nullable=True)
    denial_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    rollback_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    execution_result: Mapped[dict[str, Any]] = mapped_column(JSON_TYPE, default=dict, nullable=False)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    incident: Mapped[IncidentOrm] = relationship("IncidentOrm", back_populates="actions")


class BlocklistEntryOrm(Base):
    """Simulated firewall blocklist table."""

    __tablename__ = "blocklist_entries"

    ip_address: Mapped[str] = mapped_column(String(64), primary_key=True)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    incident_id: Mapped[uuid.UUID | None] = mapped_column(UUID_TYPE, nullable=True)
    action_id: Mapped[uuid.UUID | None] = mapped_column(UUID_TYPE, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)


class QuarantinedHostOrm(Base):
    """Simulated host isolation table."""

    __tablename__ = "quarantined_hosts"

    hostname: Mapped[str] = mapped_column(String(128), primary_key=True)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    incident_id: Mapped[uuid.UUID | None] = mapped_column(UUID_TYPE, nullable=True)
    action_id: Mapped[uuid.UUID | None] = mapped_column(UUID_TYPE, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)


class DisabledUserOrm(Base):
    """Simulated disabled user account table."""

    __tablename__ = "disabled_users"

    username: Mapped[str] = mapped_column(String(128), primary_key=True)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    incident_id: Mapped[uuid.UUID | None] = mapped_column(UUID_TYPE, nullable=True)
    action_id: Mapped[uuid.UUID | None] = mapped_column(UUID_TYPE, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)


class AuditLedgerEntryOrm(Base):
    """Cryptographic hash chain audit ledger table."""

    __tablename__ = "audit_ledger_entries"

    sequence_number: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    entry_type: Mapped[EntryType] = mapped_column(String(64), nullable=False, index=True)
    incident_id: Mapped[uuid.UUID | None] = mapped_column(UUID_TYPE, nullable=True, index=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON_TYPE, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    previous_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    entry_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    anchor_batch_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID_TYPE, ForeignKey("anchor_batches.id", ondelete="SET NULL"), nullable=True, index=True
    )


class AnchorBatchOrm(Base):
    """On-chain Merkle root anchor batches table."""

    __tablename__ = "anchor_batches"

    id: Mapped[uuid.UUID] = mapped_column(UUID_TYPE, primary_key=True, default=uuid.uuid4)
    from_sequence: Mapped[int] = mapped_column(BigInteger, nullable=False)
    to_sequence: Mapped[int] = mapped_column(BigInteger, nullable=False)
    merkle_root: Mapped[str] = mapped_column(String(66), nullable=False, index=True)
    entry_count: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[AnchorStatus] = mapped_column(
        String(32), default=AnchorStatus.PENDING, nullable=False, index=True
    )
    tx_hash: Mapped[str | None] = mapped_column(String(66), nullable=True, index=True)
    block_number: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    contract_address: Mapped[str | None] = mapped_column(String(42), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    anchored_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class EvidenceItemOrm(Base):
    """Incident evidence items stored in MinIO table."""

    __tablename__ = "evidence_items"

    id: Mapped[uuid.UUID] = mapped_column(UUID_TYPE, primary_key=True, default=uuid.uuid4)
    incident_id: Mapped[uuid.UUID] = mapped_column(
        UUID_TYPE, ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[str] = mapped_column(String(128), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    file_hash_sha256: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    storage_path: Mapped[str] = mapped_column(String(512), nullable=False)
    collected_by: Mapped[str] = mapped_column(String(64), nullable=False, default="system")
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)


class ReportOrm(Base):
    """Generated incident reports table."""

    __tablename__ = "reports"

    id: Mapped[uuid.UUID] = mapped_column(UUID_TYPE, primary_key=True, default=uuid.uuid4)
    incident_id: Mapped[uuid.UUID] = mapped_column(
        UUID_TYPE, ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    format: Mapped[str] = mapped_column(String(16), nullable=False)  # "json", "md", "pdf"
    storage_path: Mapped[str] = mapped_column(String(512), nullable=False)
    file_hash_sha256: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    file_size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    generated_by: Mapped[str] = mapped_column(String(64), nullable=False, default="system")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)


class SystemSettingOrm(Base):
    """Global system settings table (e.g. Autonomy mode)."""

    __tablename__ = "system_settings"

    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    value: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    updated_by: Mapped[str] = mapped_column(String(64), nullable=False, default="system")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
