"""API router for triggering Attack Simulator scenarios."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Annotated

# Ensure repository root is in sys.path
_REPO_ROOT = str(Path(__file__).resolve().parents[4])
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from simulator.run_scenario import load_scenario
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import require_viewer
from app.db.session import get_db_session
from app.domain.user import User
from app.repositories.event_repository import EventRepository
from app.services.detection.detection_service import DetectionService
from app.services.incident_correlation_service import IncidentCorrelationService
from app.services.ingestion.event_normalizer import EventNormalizer
from app.services.ingestion.event_publisher import EventPublisher
from app.services.response.response_orchestrator import ResponseOrchestrator

router = APIRouter(prefix="/simulator", tags=["Attack Simulator"])


class ScenarioInfo(BaseModel):
    """Scenario details and description."""

    name: str
    title: str
    description: str
    target_asset: str
    expected_priority: str
    expected_response: str


SCENARIOS_CATALOG: list[ScenarioInfo] = [
    ScenarioInfo(
        name="ssh_brute_force_compromise",
        title="SSH Brute Force with Valid Account Compromise",
        description="Multiple failed logins followed by successful login, user creation, and outbound exfiltration.",
        target_asset="web-prod-01.corp",
        expected_priority="P1",
        expected_response="Autonomous IP Block (simulated firewall)",
    ),
    ScenarioInfo(
        name="port_scan_recon",
        title="Network Port Scan Reconnaissance",
        description="Sequential port probes across multiple ports from single external IP.",
        target_asset="web-prod-01.corp",
        expected_priority="P3",
        expected_response="Alert generated, scored, correlated",
    ),
    ScenarioInfo(
        name="ransomware_activity",
        title="Ransomware Dropper & Mass File Encryption",
        description="Encoded PowerShell downloader followed by rapid file modification on Tier-0 database.",
        target_asset="db-cluster-01.corp",
        expected_priority="P1",
        expected_response="Host Isolation escalates to AWAITING_APPROVAL (high-impact guardrail)",
    ),
    ScenarioInfo(
        name="benign_admin_scan_false_positive",
        title="Benign Admin Scan from Allowlisted Subnet",
        description="Failed logins originating from trusted gateway IP (10.0.0.1).",
        target_asset="web-prod-01.corp",
        expected_priority="P3",
        expected_response="DENIED by Allowlist Guardrail (recorded in timeline and hash ledger)",
    ),
    ScenarioInfo(
        name="protected_asset_attack",
        title="Malicious Activity targeting Protected Domain Controller",
        description="Privileged attack against is_protected=True Domain Controller (dc-primary.corp).",
        target_asset="dc-primary.corp",
        expected_priority="P1",
        expected_response="AWAITING_APPROVAL (Protected Asset Guardrail)",
    ),
]


class RunScenarioResponse(BaseModel):
    """Result of launching scenario."""

    scenario_name: str
    events_injected: int
    alerts_triggered: int
    incidents_impacted: int
    status: str = "completed"


@router.get("/scenarios", response_model=list[ScenarioInfo])
async def list_scenarios(
    _: Annotated[User, Depends(require_viewer)],
) -> list[ScenarioInfo]:
    """Retrieve catalog of available attack simulation scenarios."""
    return SCENARIOS_CATALOG


@router.post("/scenarios/{scenario_name}/run", response_model=RunScenarioResponse)
async def run_scenario_endpoint(
    scenario_name: str,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[User, Depends(require_viewer)],
    speed: float = Query(1.0, ge=0.1, le=10.0),
) -> RunScenarioResponse:
    """Execute an attack simulation scenario in the environment."""
    valid_names = [s.name for s in SCENARIOS_CATALOG]
    if scenario_name not in valid_names:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "SCENARIO_NOT_FOUND",
                    "message": f"Scenario '{scenario_name}' not found",
                }
            },
        )

    raw_events = load_scenario(scenario_name)
    normalizer = EventNormalizer()
    repo = EventRepository(session)
    detection = DetectionService()
    correlation = IncidentCorrelationService(session)
    orchestrator = ResponseOrchestrator(session)
    publisher = EventPublisher()

    total_alerts = 0
    impacted_incidents: set[str] = set()

    for raw in raw_events:
        event = normalizer.normalize(raw)
        await repo.save(event)
        await publisher.publish(event)

        # Inline execution for instant feedback in UI simulation
        alerts = await detection.process_event(event, session)
        total_alerts += len(alerts)
        for alert in alerts:
            incident = await correlation.correlate_alert(alert)
            impacted_incidents.add(str(incident.id))
            await orchestrator.evaluate_incident(incident)

    await session.commit()

    return RunScenarioResponse(
        scenario_name=scenario_name,
        events_injected=len(raw_events),
        alerts_triggered=total_alerts,
        incidents_impacted=len(impacted_incidents),
        status="completed",
    )
