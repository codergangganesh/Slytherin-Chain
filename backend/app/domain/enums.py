"""Domain enumerations for SentinelChain.

Contains all standardized string enums used across domain models,
database schemas, services, and API contracts.
"""

from __future__ import annotations

from enum import StrEnum


class UserRole(StrEnum):
    """RBAC user roles with strict hierarchy."""

    VIEWER = "viewer"
    ANALYST = "analyst"
    ADMIN = "admin"


class IncidentStatus(StrEnum):
    """Lifecycle states for security incidents."""

    NEW = "NEW"
    TRIAGED = "TRIAGED"
    AWAITING_APPROVAL = "AWAITING_APPROVAL"
    CONTAINED = "CONTAINED"
    INVESTIGATING = "INVESTIGATING"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"
    FALSE_POSITIVE = "FALSE_POSITIVE"


class IncidentPriority(StrEnum):
    """Incident priority levels based on calculated risk score."""

    P1 = "P1"  # Critical (Risk Score >= 80)
    P2 = "P2"  # High (Risk Score 60-79)
    P3 = "P3"  # Medium (Risk Score 40-59)
    P4 = "P4"  # Low (Risk Score < 40)


class EventSource(StrEnum):
    """Source subsystem generating the security event."""

    SSH = "ssh"
    FIREWALL = "firewall"
    ENDPOINT = "endpoint"
    WEB = "web"
    CLOUD = "cloud"
    SIMULATOR = "simulator"


class EventType(StrEnum):
    """Standardized event types aligned with Elastic Common Schema."""

    LOGIN_FAILED = "login_failed"
    LOGIN_SUCCESS = "login_success"
    PORT_CONNECTION = "port_connection"
    PROCESS_STARTED = "process_started"
    FILE_MODIFIED = "file_modified"
    OUTBOUND_TRANSFER = "outbound_transfer"
    HTTP_REQUEST = "http_request"
    USER_CREATED = "user_created"


class RuleType(StrEnum):
    """Detection rule evaluation strategies."""

    MATCH = "match"
    THRESHOLD = "threshold"
    DISTINCT_COUNT = "distinct_count"
    SEQUENCE = "sequence"


class ActionType(StrEnum):
    """Autonomous response action types."""

    BLOCK_IP = "block_ip"
    ISOLATE_HOST = "isolate_host"
    DISABLE_USER = "disable_user"
    RESTRICT_ACCESS = "restrict_access"
    NOTIFY = "notify"


class ActionStatus(StrEnum):
    """Lifecycle status of a response action."""

    PROPOSED = "PROPOSED"
    AWAITING_APPROVAL = "AWAITING_APPROVAL"
    APPROVED = "APPROVED"
    DENIED = "DENIED"
    EXECUTING = "EXECUTING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    ROLLED_BACK = "ROLLED_BACK"
    EXPIRED = "EXPIRED"


class EntryType(StrEnum):
    """Audit ledger entry classifications for cryptographic chaining."""

    INCIDENT_CREATED = "INCIDENT_CREATED"
    ALERT_ATTACHED = "ALERT_ATTACHED"
    SCORE_CHANGED = "SCORE_CHANGED"
    STATE_TRANSITION = "STATE_TRANSITION"
    ACTION_PROPOSED = "ACTION_PROPOSED"
    ACTION_APPROVED = "ACTION_APPROVED"
    ACTION_DENIED = "ACTION_DENIED"
    ACTION_EXECUTED = "ACTION_EXECUTED"
    ACTION_FAILED = "ACTION_FAILED"
    ACTION_ROLLED_BACK = "ACTION_ROLLED_BACK"
    ACTION_EXPIRED = "ACTION_EXPIRED"
    NOTE_ADDED = "NOTE_ADDED"
    EVIDENCE_ADDED = "EVIDENCE_ADDED"
    REPORT_GENERATED = "REPORT_GENERATED"
    AUTONOMY_MODE_CHANGED = "AUTONOMY_MODE_CHANGED"


class AnchorStatus(StrEnum):
    """Status of an on-chain Merkle root anchor batch."""

    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    FAILED = "FAILED"


class VerificationStatus(StrEnum):
    """Integrity verification verdict status."""

    VERIFIED = "VERIFIED"
    TAMPERED = "TAMPERED"
    PENDING_ANCHOR = "PENDING_ANCHOR"
    CHAIN_UNAVAILABLE = "CHAIN_UNAVAILABLE"


class AssetEnvironment(StrEnum):
    """Operating environment of an asset."""

    PRODUCTION = "production"
    STAGING = "staging"
    DEVELOPMENT = "development"
    DMZ = "dmz"
    INTERNAL = "internal"
