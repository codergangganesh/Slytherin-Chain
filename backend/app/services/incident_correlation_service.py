"""Incident correlation and scoring orchestrator."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import get_settings
from app.domain.alert import Alert
from app.domain.enums import EntryType, IncidentStatus
from app.domain.incident import Incident
from app.repositories.alert_repository import AlertRepository
from app.repositories.incident_repository import IncidentRepository
from app.services.enrichment.asset_context_service import AssetContextService
from app.services.enrichment.threat_intel_service import ThreatIntelService
from app.services.integrity.hash_chain_ledger import HashChainLedger
from app.services.risk_scoring_service import calculate_risk_score


class IncidentCorrelationService:
    """Correlates detection alerts into unified incidents and manages timeline & scoring."""

    def __init__(
        self,
        session: AsyncSession,
        threat_intel_service: ThreatIntelService | None = None,
        asset_context_service: AssetContextService | None = None,
        ledger: HashChainLedger | None = None,
    ) -> None:
        self._session = session
        self._incident_repo = IncidentRepository(session)
        self._alert_repo = AlertRepository(session)
        self._threat_intel = threat_intel_service or ThreatIntelService(session=session)
        self._asset_context = asset_context_service or AssetContextService(session=session)
        self._ledger = ledger or HashChainLedger(session)
        self._settings = get_settings()

    async def correlate_alert(self, alert: Alert) -> Incident:
        """Correlate a single alert into an existing open incident or create a new one.

        Args:
            alert: The newly generated alert.

        Returns:
            Incident: The created or updated incident entity.
        """
        # Determine correlation targets
        src_ip = alert.group_by_key if "." in alert.group_by_key else None
        host = (
            alert.group_by_key
            if ("." not in alert.group_by_key and not alert.group_by_key.startswith("user:"))
            else None
        )
        username = (
            alert.group_by_key.replace("user:", "")
            if alert.group_by_key.startswith("user:")
            else None
        )

        # Gather Enrichment Context
        intel_rep = 0.1
        if src_ip:
            intel = await self._threat_intel.get_ip_reputation(src_ip)
            intel_rep = intel.reputation_score

        asset_ctx = await self._asset_context.get_context_by_host(host)

        # Check correlation window
        cutoff = datetime.now(UTC) - timedelta(seconds=self._settings.correlation_window_seconds)
        existing = await self._incident_repo.find_open_incident_by_correlation_key(
            src_ip=src_ip,
            host=host,
            username=username,
            correlation_cutoff=cutoff,
        )

        if existing:
            # Correlate to existing incident
            await self._incident_repo.link_alert(existing.id, alert.id)
            existing_alerts = await self._alert_repo.list_alerts_by_incident(existing.id)

            # Re-score with correlation bonus
            score_res = calculate_risk_score(
                severity=max(alert.severity, existing.risk_score / 100.0),
                confidence=max(alert.confidence, 0.7),
                asset_criticality=asset_ctx.criticality,
                exposure=asset_ctx.exposure_score,
                intel_reputation=intel_rep,
                additional_alert_count=max(0, len(existing_alerts) - 1),
                settings=self._settings,
            )

            # Accumulate tactics and techniques
            tactics = list(set(existing.mitre_tactics + [alert.mitre.tactic]))
            techniques = list(
                set(
                    existing.mitre_techniques
                    + [f"{alert.mitre.technique_id} - {alert.mitre.technique_name}"]
                )
            )

            updated_incident = await self._incident_repo.update_incident(
                incident_id=existing.id,
                priority=score_res.priority,
                risk_score=score_res.score,
                risk_breakdown={
                    "score": score_res.score,
                    "priority": score_res.priority.value,
                    "correlation_bonus": score_res.correlation_bonus,
                    "summary": score_res.summary,
                    "factors": [
                        {
                            "factor_name": f.factor_name,
                            "raw_value": f.raw_value,
                            "weight": f.weight,
                            "contribution": f.contribution,
                            "explanation": f.explanation,
                        }
                        for f in score_res.factors
                    ],
                },
                mitre_tactics=tactics,
                mitre_techniques=techniques,
            )

            # Add timeline entry
            await self._incident_repo.add_timeline_entry(
                incident_id=existing.id,
                entry_type="ALERT_CORRELATED",
                title=f"Secondary Alert Correlated: {alert.title}",
                description=f"Correlated alert from rule {alert.rule_id} with severity {alert.severity:.2f}. New risk score: {score_res.score}",
                actor="detection_engine",
                mitre_tactic=alert.mitre.tactic,
                mitre_technique=alert.mitre.technique_id,
                metadata={
                    "alert_id": str(alert.id),
                    "rule_id": alert.rule_id,
                    "risk_score": score_res.score,
                },
            )

            # Append to audit ledger
            await self._ledger.append_entry(
                entry_type=EntryType.ALERT_ATTACHED,
                incident_id=existing.id,
                payload={"alert_id": str(alert.id), "rule_id": alert.rule_id, "title": alert.title},
            )
            await self._ledger.append_entry(
                entry_type=EntryType.SCORE_CHANGED,
                incident_id=existing.id,
                payload={
                    "old_score": existing.risk_score,
                    "new_score": score_res.score,
                    "priority": score_res.priority.value,
                },
            )

            assert updated_incident is not None
            return updated_incident

        else:
            # Create new incident
            score_res = calculate_risk_score(
                severity=alert.severity,
                confidence=alert.confidence,
                asset_criticality=asset_ctx.criticality,
                exposure=asset_ctx.exposure_score,
                intel_reputation=intel_rep,
                additional_alert_count=0,
                settings=self._settings,
            )

            affected_assets = [str(asset_ctx.asset_id)] if asset_ctx.asset_id else []

            new_incident = await self._incident_repo.create(
                title=f"{alert.title} against {alert.group_by_key}",
                description=alert.description,
                status=IncidentStatus.TRIAGED,
                priority=score_res.priority,
                risk_score=score_res.score,
                risk_breakdown={
                    "score": score_res.score,
                    "priority": score_res.priority.value,
                    "correlation_bonus": score_res.correlation_bonus,
                    "summary": score_res.summary,
                    "factors": [
                        {
                            "factor_name": f.factor_name,
                            "raw_value": f.raw_value,
                            "weight": f.weight,
                            "contribution": f.contribution,
                            "explanation": f.explanation,
                        }
                        for f in score_res.factors
                    ],
                },
                primary_src_ip=src_ip,
                primary_host=host,
                primary_username=username,
                mitre_tactics=[alert.mitre.tactic],
                mitre_techniques=[f"{alert.mitre.technique_id} - {alert.mitre.technique_name}"],
                affected_asset_ids=affected_assets,
            )

            await self._incident_repo.link_alert(new_incident.id, alert.id)

            # Add initial timeline entry
            await self._incident_repo.add_timeline_entry(
                incident_id=new_incident.id,
                entry_type="INCIDENT_CREATED",
                title=f"Incident Created: {alert.title}",
                description=f"Initial alert triggered by rule {alert.rule_id}. Calculated Priority {score_res.priority.value} (Score {score_res.score}).",
                actor="detection_engine",
                mitre_tactic=alert.mitre.tactic,
                mitre_technique=alert.mitre.technique_id,
                metadata={
                    "alert_id": str(alert.id),
                    "rule_id": alert.rule_id,
                    "initial_score": score_res.score,
                },
            )

            # Append to audit ledger
            await self._ledger.append_entry(
                entry_type=EntryType.INCIDENT_CREATED,
                incident_id=new_incident.id,
                payload={
                    "reference_id": new_incident.reference_id,
                    "title": new_incident.title,
                    "priority": score_res.priority.value,
                    "risk_score": score_res.score,
                },
            )

            return new_incident
