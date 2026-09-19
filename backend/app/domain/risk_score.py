"""Domain model for Risk Scoring and factor breakdown."""

from __future__ import annotations

from dataclasses import dataclass

from app.domain.enums import IncidentPriority


@dataclass(frozen=True)
class RiskFactorContribution:
    """Individual component contributing to the total risk score."""

    factor_name: str
    raw_value: float
    weight: float
    contribution: float
    explanation: str


@dataclass(frozen=True)
class RiskScoreResult:
    """Complete risk scoring output with explainable breakdown and priority assignment."""

    score: float  # 0.0 - 100.0
    priority: IncidentPriority
    factors: list[RiskFactorContribution]
    correlation_bonus: float
    summary: str
