"""Unit tests for Incident State Machine legal and illegal transitions."""

from __future__ import annotations

import pytest

from app.domain.enums import IncidentStatus, UserRole
from app.domain.exceptions import AuthorizationError, InvalidStateTransitionError
from app.domain.incident_state_machine import validate_state_transition


def test_legal_automatic_transitions() -> None:
    """Test valid automatic pipeline transitions."""
    # NEW -> TRIAGED
    validate_state_transition(
        current_status=IncidentStatus.NEW,
        target_status=IncidentStatus.TRIAGED,
        is_automated=True,
    )
    # TRIAGED -> CONTAINED
    validate_state_transition(
        current_status=IncidentStatus.TRIAGED,
        target_status=IncidentStatus.CONTAINED,
        is_automated=True,
    )


def test_illegal_state_transition() -> None:
    """Test that skipping states or reverting closed incidents raises an exception."""
    with pytest.raises(InvalidStateTransitionError):
        validate_state_transition(
            current_status=IncidentStatus.NEW,
            target_status=IncidentStatus.CLOSED,
            user_role=UserRole.ADMIN,
        )

    with pytest.raises(InvalidStateTransitionError):
        validate_state_transition(
            current_status=IncidentStatus.CLOSED,
            target_status=IncidentStatus.INVESTIGATING,
            user_role=UserRole.ADMIN,
        )


def test_role_authorization_on_manual_transition() -> None:
    """Test that viewer role cannot manually transition incident state."""
    with pytest.raises(AuthorizationError):
        validate_state_transition(
            current_status=IncidentStatus.TRIAGED,
            target_status=IncidentStatus.INVESTIGATING,
            user_role=UserRole.VIEWER,
            is_automated=False,
        )


def test_resolution_notes_mandatory_for_closure() -> None:
    """Test that closing an incident requires non-empty resolution notes."""
    with pytest.raises(InvalidStateTransitionError):
        validate_state_transition(
            current_status=IncidentStatus.RESOLVED,
            target_status=IncidentStatus.CLOSED,
            user_role=UserRole.ANALYST,
            notes="",
        )

    # Valid with notes
    validate_state_transition(
        current_status=IncidentStatus.RESOLVED,
        target_status=IncidentStatus.CLOSED,
        user_role=UserRole.ANALYST,
        notes="Root cause identified and firewall rules updated.",
    )
