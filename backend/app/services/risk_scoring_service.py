"""Pure risk scoring calculation service and factor breakdown."""

from __future__ import annotations

from app.config.settings import Settings, get_settings
from app.domain.enums import IncidentPriority
from app.domain.risk_score import RiskFactorContribution, RiskScoreResult


def clamp(val: float, min_val: float = 0.0, max_val: float = 1.0) -> float:
    """Clamp a floating point value between min_val and max_val."""
    return max(min_val, min(val, max_val))


def determine_priority(score: float) -> IncidentPriority:
    """Map numeric risk score (0-100) to Incident Priority (P1-P4)."""
    if score >= 80.0:
        return IncidentPriority.P1
    elif score >= 60.0:
        return IncidentPriority.P2
    elif score >= 40.0:
        return IncidentPriority.P3
    return IncidentPriority.P4


def calculate_risk_score(
    severity: float,
    confidence: float,
    asset_criticality: int,
    exposure: float,
    intel_reputation: float,
    additional_alert_count: int = 0,
    settings: Settings | None = None,
) -> RiskScoreResult:
    """Calculate the explainable risk score and priority for an incident.

    Formula:
        risk_score = 100 * clamp(
            W_SEVERITY   * severity
          + W_CONFIDENCE * confidence
          + W_ASSET      * (asset_criticality / 5)
          + W_EXPOSURE   * exposure
          + W_INTEL      * intel_reputation
          + CORRELATION_BONUS
        , 0, 1)

    Args:
        severity: Rule severity (0.0 - 1.0).
        confidence: Rule confidence (0.0 - 1.0).
        asset_criticality: Target asset criticality (1 - 5).
        exposure: Network exposure factor (1.0 internet-facing, 0.5 internal, 0.2 isolated).
        intel_reputation: Threat intel malicious reputation (0.0 - 1.0).
        additional_alert_count: Number of correlated secondary alerts (gives up to +0.15 bonus).
        settings: Application settings containing configurable weights.

    Returns:
        RiskScoreResult: Complete explainable score, priority, and factor breakdown.
    """
    cfg = settings or get_settings()

    # Normalize inputs
    norm_severity = clamp(severity, 0.0, 1.0)
    norm_confidence = clamp(confidence, 0.0, 1.0)
    norm_asset = clamp(asset_criticality / 5.0, 0.2, 1.0)
    norm_exposure = clamp(exposure, 0.2, 1.0)
    norm_intel = clamp(intel_reputation, 0.0, 1.0)

    # Weights
    w_sev = cfg.risk_weight_severity
    w_conf = cfg.risk_weight_confidence
    w_asset = cfg.risk_weight_asset
    w_exp = cfg.risk_weight_exposure
    w_intel = cfg.risk_weight_intel

    # Correlation bonus: +0.05 per additional distinct alert, max +0.15
    correlation_bonus = min(0.15, max(0.0, additional_alert_count * 0.05))

    # Contributions
    c_sev = w_sev * norm_severity
    c_conf = w_conf * norm_confidence
    c_asset = w_asset * norm_asset
    c_exp = w_exp * norm_exposure
    c_intel = w_intel * norm_intel

    raw_sum = c_sev + c_conf + c_asset + c_exp + c_intel + correlation_bonus
    clamped_ratio = clamp(raw_sum, 0.0, 1.0)
    final_score = round(clamped_ratio * 100.0, 1)
    priority = determine_priority(final_score)

    factors = [
        RiskFactorContribution(
            factor_name="Threat Severity",
            raw_value=norm_severity,
            weight=w_sev,
            contribution=round(c_sev * 100.0, 1),
            explanation=f"Rule severity {norm_severity:.2f} (weight {w_sev:.2f})",
        ),
        RiskFactorContribution(
            factor_name="Detection Confidence",
            raw_value=norm_confidence,
            weight=w_conf,
            contribution=round(c_conf * 100.0, 1),
            explanation=f"Rule confidence {norm_confidence:.2f} (weight {w_conf:.2f})",
        ),
        RiskFactorContribution(
            factor_name="Asset Criticality",
            raw_value=norm_asset,
            weight=w_asset,
            contribution=round(c_asset * 100.0, 1),
            explanation=f"Asset criticality {asset_criticality}/5 (weight {w_asset:.2f})",
        ),
        RiskFactorContribution(
            factor_name="Network Exposure",
            raw_value=norm_exposure,
            weight=w_exp,
            contribution=round(c_exp * 100.0, 1),
            explanation=f"Exposure level {norm_exposure:.2f} (weight {w_exp:.2f})",
        ),
        RiskFactorContribution(
            factor_name="Threat Intelligence",
            raw_value=norm_intel,
            weight=w_intel,
            contribution=round(c_intel * 100.0, 1),
            explanation=f"Reputation score {norm_intel:.2f} (weight {w_intel:.2f})",
        ),
    ]

    summary = (
        f"Calculated {priority.value} incident priority with risk score {final_score}/100. "
        f"Primary drivers: Severity (+{round(c_sev * 100, 1)}), Asset (+{round(c_asset * 100, 1)}), "
        f"Intel (+{round(c_intel * 100, 1)})."
    )

    return RiskScoreResult(
        score=final_score,
        priority=priority,
        factors=factors,
        correlation_bonus=round(correlation_bonus * 100.0, 1),
        summary=summary,
    )
