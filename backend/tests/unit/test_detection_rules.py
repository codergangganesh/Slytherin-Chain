"""Unit tests for Detection Rule evaluation across match, threshold, and sequence types."""

from __future__ import annotations

from datetime import datetime, timezone
import uuid
import pytest

from app.domain.enums import EventSource, EventType, RuleType
from app.domain.normalized_event import NormalizedEvent
from app.services.detection.rule_evaluator import RuleEvaluator
from app.services.detection.rule_loader import DetectionRuleConfig, MitreConfig
from app.services.detection.sliding_window_counter import SlidingWindowCounter


@pytest.mark.asyncio
async def test_match_rule_powershell_regex() -> None:
    """Test match rule detecting encoded PowerShell execution."""
    rule = DetectionRuleConfig(
        id="POWERSHELL-004",
        title="Suspicious Encoded PowerShell Execution",
        description="Execution of PowerShell with encoded commands",
        type=RuleType.MATCH,
        severity=0.8,
        confidence=0.85,
        match={
            "event_type": "process_started",
            "process_name": "powershell.exe",
            "command_line_regex": "(?i)(-enc|-encodedcommand|downloadstring)",
        },
        group_by="host",
        mitre=MitreConfig(tactic="Execution", technique_id="T1059.001", technique_name="PowerShell"),
        playbook_category="malware",
    )

    evaluator = RuleEvaluator(window_counter=SlidingWindowCounter())

    # Matching event
    event_match = NormalizedEvent(
        event_id=uuid.uuid4(),
        occurred_at=datetime.now(timezone.utc),
        ingested_at=datetime.now(timezone.utc),
        source=EventSource.ENDPOINT,
        event_type=EventType.PROCESS_STARTED,
        host="web-prod-01.corp",
        process_name="powershell.exe",
        command_line="powershell.exe -enc SQBFAFgAIAAoAE4AZQB3...",
    )

    alert = await evaluator.evaluate(event_match, rule)
    assert alert is not None
    assert alert.rule_id == "POWERSHELL-004"
    assert alert.severity == 0.8

    # Non-matching event (benign notepad)
    event_benign = NormalizedEvent(
        event_id=uuid.uuid4(),
        occurred_at=datetime.now(timezone.utc),
        ingested_at=datetime.now(timezone.utc),
        source=EventSource.ENDPOINT,
        event_type=EventType.PROCESS_STARTED,
        host="web-prod-01.corp",
        process_name="notepad.exe",
        command_line="notepad.exe document.txt",
    )

    alert2 = await evaluator.evaluate(event_benign, rule)
    assert alert2 is None


@pytest.mark.asyncio
async def test_threshold_rule_evaluation() -> None:
    """Test threshold rule counting events within sliding window."""
    rule = DetectionRuleConfig(
        id="SSH-BRUTE-001",
        title="SSH Brute Force",
        description="Many failed SSH logins",
        type=RuleType.THRESHOLD,
        severity=0.6,
        confidence=0.7,
        match={"event_type": "login_failed", "source": "ssh"},
        group_by="src_ip",
        threshold=3,
        window_seconds=60,
        mitre=MitreConfig(tactic="Credential Access", technique_id="T1110", technique_name="Brute Force"),
        playbook_category="brute_force",
    )

    counter = SlidingWindowCounter()
    evaluator = RuleEvaluator(window_counter=counter)
    attacker_ip = "198.51.100.42"

    for i in range(2):
        ev = NormalizedEvent(
            event_id=uuid.uuid4(),
            occurred_at=datetime.now(timezone.utc),
            ingested_at=datetime.now(timezone.utc),
            source=EventSource.SSH,
            event_type=EventType.LOGIN_FAILED,
            src_ip=attacker_ip,
        )
        alert = await evaluator.evaluate(ev, rule)
        assert alert is None  # Below threshold

    # 3rd event trips threshold
    ev3 = NormalizedEvent(
        event_id=uuid.uuid4(),
        occurred_at=datetime.now(timezone.utc),
        ingested_at=datetime.now(timezone.utc),
        source=EventSource.SSH,
        event_type=EventType.LOGIN_FAILED,
        src_ip=attacker_ip,
    )
    alert3 = await evaluator.evaluate(ev3, rule)
    assert alert3 is not None
    assert alert3.rule_id == "SSH-BRUTE-001"
    assert len(alert3.matched_event_ids) == 3
