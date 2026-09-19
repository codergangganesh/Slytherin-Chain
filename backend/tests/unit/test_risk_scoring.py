"""Unit tests for pure risk scoring calculations and factor breakdowns."""

from __future__ import annotations

import pytest

from app.domain.enums import IncidentPriority
from app.services.risk_scoring_service import calculate_risk_score, clamp, determine_priority


def test_clamp_function() -> None:
    """Test clamping within boundaries."""
    assert clamp(1.5, 0.0, 1.0) == 1.0
    assert clamp(-0.5, 0.0, 1.0) == 0.0
    assert clamp(0.5, 0.0, 1.0) == 0.5


def test_priority_determination() -> None:
    """Test priority boundary mappings."""
    assert determine_priority(80.0) == IncidentPriority.P1
    assert determine_priority(79.9) == IncidentPriority.P2
    assert determine_priority(60.0) == IncidentPriority.P2
    assert determine_priority(59.9) == IncidentPriority.P3
    assert determine_priority(40.0) == IncidentPriority.P3
    assert determine_priority(39.9) == IncidentPriority.P4
    assert determine_priority(0.0) == IncidentPriority.P4


def test_calculate_risk_score_high_criticality_attack() -> None:
    """Test risk calculation for a critical attack on a tier-0 protected asset."""
    res = calculate_risk_score(
        severity=0.9,
        confidence=0.85,
        asset_criticality=5,
        exposure=1.0,
        intel_reputation=0.95,
        additional_alert_count=2,
    )
    # Severity: 0.3*0.9 = 0.27
    # Conf: 0.2*0.85 = 0.17
    # Asset: 0.25*(5/5) = 0.25
    # Exp: 0.1*1.0 = 0.10
    # Intel: 0.15*0.95 = 0.1425
    # Bonus: 2*0.05 = 0.10
    # Sum = 1.0325 -> clamped 1.0 -> 100.0 score -> P1
    assert res.score == 100.0
    assert res.priority == IncidentPriority.P1
    assert len(res.factors) == 5
    assert res.correlation_bonus == 10.0


def test_calculate_risk_score_low_impact() -> None:
    """Test low risk calculation on internal workstation."""
    res = calculate_risk_score(
        severity=0.2,
        confidence=0.5,
        asset_criticality=1,
        exposure=0.2,
        intel_reputation=0.0,
        additional_alert_count=0,
    )
    assert res.score < 40.0
    assert res.priority == IncidentPriority.P4
