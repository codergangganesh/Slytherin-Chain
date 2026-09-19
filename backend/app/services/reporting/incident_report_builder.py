"""Incident report builder compiling all 9 required sections."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.orm_models import (
    AnchorBatchOrm,
    AuditLedgerEntryOrm,
    EvidenceItemOrm,
    ResponseActionOrm,
)
from app.domain.exceptions import EntityNotFoundError
from app.repositories.alert_repository import AlertRepository
from app.repositories.asset_repository import AssetRepository
from app.repositories.incident_repository import IncidentRepository
from app.services.integrity.integrity_verification_service import (
    IntegrityVerificationService,
)
from app.services.reporting.executive_summary_generator import (
    ExecutiveSummaryGenerator,
)


@dataclass
class IncidentReportDocument:
    """Structured incident report containing all 9 sections."""

    schema_version: str
    generated_at: datetime
    executive_summary: str
    metadata: dict[str, Any]
    threat_details: dict[str, Any]
    attack_sequence: list[dict[str, Any]]
    affected_assets_and_impact: dict[str, Any]
    evidence: list[dict[str, Any]]
    response_actions: list[dict[str, Any]]
    resolution_and_recommendations: dict[str, Any]
    integrity_attestation: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        """Convert report document to JSON serializable dictionary."""
        return {
            "schema_version": self.schema_version,
            "generated_at": self.generated_at.isoformat(),
            "executive_summary": self.executive_summary,
            "metadata": self.metadata,
            "threat_details": self.threat_details,
            "attack_sequence": self.attack_sequence,
            "affected_assets_and_impact": self.affected_assets_and_impact,
            "evidence": self.evidence,
            "response_actions": self.response_actions,
            "resolution_and_recommendations": self.resolution_and_recommendations,
            "integrity_attestation": self.integrity_attestation,
        }


class IncidentReportBuilder:
    """Assembles comprehensive structured incident reports."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._incident_repo = IncidentRepository(session)
        self._alert_repo = AlertRepository(session)
        self._asset_repo = AssetRepository(session)
        self._verification_service = IntegrityVerificationService(session)
        self._summary_gen = ExecutiveSummaryGenerator()

    async def build_report(self, incident_id: UUID) -> IncidentReportDocument:
        """Construct full report document for an incident."""
        incident = await self._incident_repo.get_by_id(incident_id)
        if not incident:
            raise EntityNotFoundError("Incident", str(incident_id))

        now = datetime.now(timezone.utc)
        alerts = await self._alert_repo.list_alerts_by_incident(incident_id)
        timeline = await self._incident_repo.list_timeline(incident_id)

        # 1. Fetch Actions
        stmt_actions = select(ResponseActionOrm).where(ResponseActionOrm.incident_id == incident_id)
        res_actions = await self._session.execute(stmt_actions)
        actions = res_actions.scalars().all()
        actions_list = [
            {
                "id": str(a.id),
                "action_type": a.action_type,
                "target": a.target,
                "status": a.status,
                "ttl_seconds": a.ttl_seconds,
                "executed_at": a.executed_at.isoformat() if a.executed_at else None,
                "approved_by": a.approved_by,
                "denial_reason": a.denial_reason,
                "guardrail_decisions": a.guardrail_decisions,
            }
            for a in actions
        ]

        # 2. Executive Summary
        exec_summary = self._summary_gen.generate_summary(
            reference_id=incident.reference_id,
            title=incident.title,
            priority=incident.priority.value,
            risk_score=incident.risk_score,
            tactics=incident.mitre_tactics,
            primary_attacker=incident.primary_src_ip,
            primary_target=incident.primary_host,
            actions_taken=actions_list,
            status=incident.status.value,
        )

        # 3. Metadata
        duration_seconds = (
            (incident.closed_at - incident.created_at).total_seconds()
            if incident.closed_at
            else (now - incident.created_at).total_seconds()
        )
        meta = {
            "incident_id": str(incident.id),
            "reference_id": incident.reference_id,
            "title": incident.title,
            "priority": incident.priority.value,
            "risk_score": incident.risk_score,
            "status": incident.status.value,
            "assigned_to": incident.assigned_to,
            "first_seen": incident.created_at.isoformat(),
            "last_updated": incident.updated_at.isoformat(),
            "duration_seconds": int(duration_seconds),
            "risk_breakdown": {
                "score": incident.risk_breakdown.score,
                "priority": incident.risk_breakdown.priority.value,
                "correlation_bonus": incident.risk_breakdown.correlation_bonus,
                "summary": incident.risk_breakdown.summary,
                "factors": [
                    {
                        "factor_name": f.factor_name,
                        "raw_value": f.raw_value,
                        "weight": f.weight,
                        "contribution": f.contribution,
                        "explanation": f.explanation,
                    }
                    for f in incident.risk_breakdown.factors
                ],
            },
        }

        # 4. Threat Details
        iocs: dict[str, list[str]] = {"src_ips": [], "hosts": [], "usernames": []}
        if incident.primary_src_ip:
            iocs["src_ips"].append(incident.primary_src_ip)
        if incident.primary_host:
            iocs["hosts"].append(incident.primary_host)
        if incident.primary_username:
            iocs["usernames"].append(incident.primary_username)

        rules_fired = [
            {
                "rule_id": a.rule_id,
                "title": a.title,
                "severity": a.severity,
                "confidence": a.confidence,
                "tactic": a.mitre.tactic,
                "technique": f"{a.mitre.technique_id} - {a.mitre.technique_name}",
            }
            for a in alerts
        ]

        threat_details = {
            "rules_fired": rules_fired,
            "mitre_tactics": incident.mitre_tactics,
            "mitre_techniques": incident.mitre_techniques,
            "indicators_of_compromise": iocs,
        }

        # 5. Attack Sequence
        attack_seq = [
            {
                "timestamp": t.timestamp.isoformat(),
                "entry_type": t.entry_type,
                "title": t.title,
                "description": t.description,
                "actor": t.actor,
                "mitre_tactic": t.mitre_tactic,
                "mitre_technique": t.mitre_technique,
            }
            for t in timeline
        ]

        # 6. Affected Assets & Impact
        assets_info = []
        for aid in incident.affected_asset_ids:
            asset = await self._asset_repo.get_by_id(aid)
            if asset:
                assets_info.append({
                    "id": str(asset.id),
                    "hostname": asset.hostname,
                    "ip_address": asset.ip_address,
                    "criticality": asset.criticality,
                    "environment": asset.environment.value,
                    "is_protected": asset.is_protected,
                    "is_internet_facing": asset.is_internet_facing,
                    "owner": asset.owner,
                })

        business_impact = "Low operational impact; suspicious activity contained."
        if incident.risk_score >= 80:
            business_impact = "Severe potential impact to enterprise assets; high priority containment enforced."
        elif incident.risk_score >= 60:
            business_impact = "Elevated threat impact; containment or isolation active."

        assets_impact = {
            "assets": assets_info,
            "business_impact_statement": business_impact,
        }

        # 7. Evidence
        stmt_ev = select(EvidenceItemOrm).where(EvidenceItemOrm.incident_id == incident_id)
        res_ev = await self._session.execute(stmt_ev)
        evidence_items = res_ev.scalars().all()
        evidence_list = [
            {
                "id": str(e.id),
                "filename": e.filename,
                "file_hash_sha256": e.file_hash_sha256,
                "file_size_bytes": e.file_size_bytes,
                "collected_by": e.collected_by,
                "created_at": e.created_at.isoformat(),
            }
            for e in evidence_items
        ]

        # 8. Resolution & Recommendations
        recommendations = [
            "Review and rotate compromised credentials if applicable.",
            "Verify endpoint firewall and endpoint protection agent definitions.",
            "Audit access logs for additional reconnaissance across subnet.",
        ]
        res_notes = incident.close_notes or "Under active analyst investigation."
        resolution_rec = {
            "resolution_notes": res_notes,
            "recommendations": recommendations,
        }

        # 9. Integrity Attestation
        verif_status = await self._verification_service.verify_ledger()

        # Find latest anchor batch
        stmt_batch = select(AnchorBatchOrm).order_by(AnchorBatchOrm.created_at.desc()).limit(1)
        res_b = await self._session.execute(stmt_batch)
        latest_batch = res_b.scalar_one_or_none()

        stmt_ledger = (
            select(AuditLedgerEntryOrm)
            .where(AuditLedgerEntryOrm.incident_id == incident_id)
            .order_by(AuditLedgerEntryOrm.sequence_number.asc())
        )
        res_l = await self._session.execute(stmt_ledger)
        inc_ledger_entries = res_l.scalars().all()

        seq_from = inc_ledger_entries[0].sequence_number if inc_ledger_entries else 0
        seq_to = inc_ledger_entries[-1].sequence_number if inc_ledger_entries else 0

        attestation = {
            "ledger_sequence_from": seq_from,
            "ledger_sequence_to": seq_to,
            "chain_head_hash": verif_status.chain_head_hash,
            "merkle_root": latest_batch.merkle_root if latest_batch else "0x0000000000000000000000000000000000000000000000000000000000000000",
            "tx_hash": latest_batch.tx_hash if latest_batch else None,
            "block_number": latest_batch.block_number if latest_batch else None,
            "verification_status": verif_status.status.value,
            "attested_at": now.isoformat(),
        }

        return IncidentReportDocument(
            schema_version="1.0.0",
            generated_at=now,
            executive_summary=exec_summary,
            metadata=meta,
            threat_details=threat_details,
            attack_sequence=attack_seq,
            affected_assets_and_impact=assets_impact,
            evidence=evidence_list,
            response_actions=actions_list,
            resolution_and_recommendations=resolution_rec,
            integrity_attestation=attestation,
        )
