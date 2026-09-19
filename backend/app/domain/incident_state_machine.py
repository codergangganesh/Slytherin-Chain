"""Pure domain state machine for Incident Lifecycle transitions.

Enforces strictly allowed transitions and role permission boundaries.
"""

from __future__ import annotations

from app.domain.enums import IncidentStatus, UserRole
from app.domain.exceptions import AuthorizationError, InvalidStateTransitionError

# Legal state transitions map
VALID_TRANSITIONS: dict[IncidentStatus, set[IncidentStatus]] = {
    IncidentStatus.NEW: {
        IncidentStatus.TRIAGED,
        IncidentStatus.FALSE_POSITIVE,
    },
    IncidentStatus.TRIAGED: {
        IncidentStatus.CONTAINED,
        IncidentStatus.AWAITING_APPROVAL,
        IncidentStatus.INVESTIGATING,
        IncidentStatus.FALSE_POSITIVE,
    },
    IncidentStatus.AWAITING_APPROVAL: {
        IncidentStatus.CONTAINED,
        IncidentStatus.INVESTIGATING,
        IncidentStatus.FALSE_POSITIVE,
    },
    IncidentStatus.CONTAINED: {
        IncidentStatus.INVESTIGATING,
        IncidentStatus.RESOLVED,
    },
    IncidentStatus.INVESTIGATING: {
        IncidentStatus.CONTAINED,
        IncidentStatus.RESOLVED,
        IncidentStatus.FALSE_POSITIVE,
    },
    IncidentStatus.RESOLVED: {
        IncidentStatus.CLOSED,
        IncidentStatus.INVESTIGATING,  # Reopen
    },
    IncidentStatus.CLOSED: set(),  # Terminal state
    IncidentStatus.FALSE_POSITIVE: set(),  # Terminal state
}

# Manual transitions that require at least ANALYST role
ROLES_ALLOWED_MANUAL_TRANSITION: set[UserRole] = {
    UserRole.ANALYST,
    UserRole.ADMIN,
}


def validate_state_transition(
    current_status: IncidentStatus,
    target_status: IncidentStatus,
    user_role: UserRole | None = None,
    is_automated: bool = False,
    notes: str | None = None,
) -> None:
    """Validate whether an incident state transition is permissible.

    Args:
        current_status: The current status of the incident.
        target_status: The desired destination status.
        user_role: Role of the acting user if manual transition.
        is_automated: True if triggered by automated pipeline/rules.
        notes: Required notes for manual state changes.

    Raises:
        InvalidStateTransitionError: If the transition is illegal.
        AuthorizationError: If user lacks required role.
    """
    allowed_targets = VALID_TRANSITIONS.get(current_status, set())
    if target_status not in allowed_targets:
        raise InvalidStateTransitionError(
            from_state=current_status.value,
            to_state=target_status.value,
            reason=f"Permissible targets from '{current_status.value}' are {[s.value for s in allowed_targets]}",
        )

    # Validate permissions for manual actions
    if not is_automated:
        if user_role is None or user_role not in ROLES_ALLOWED_MANUAL_TRANSITION:
            raise AuthorizationError(
                "Only analysts or admins can perform manual state transitions."
            )
        if target_status in (
            IncidentStatus.RESOLVED,
            IncidentStatus.CLOSED,
            IncidentStatus.FALSE_POSITIVE,
        ):
            if not notes or not notes.strip():
                raise InvalidStateTransitionError(
                    from_state=current_status.value,
                    to_state=target_status.value,
                    reason=f"Transition to {target_status.value} requires descriptive resolution notes.",
                )
