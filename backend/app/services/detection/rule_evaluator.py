"""Rule evaluation engine implementing match, threshold, distinct_count, and sequence rules."""

from __future__ import annotations

import re
from typing import Any
import uuid

from app.domain.alert import Alert, MitreAttackMapping
from app.domain.enums import RuleType
from app.domain.normalized_event import NormalizedEvent
from app.services.detection.rule_loader import DetectionRuleConfig
from app.services.detection.sliding_window_counter import SlidingWindowCounter


class RuleEvaluator:
    """Evaluates normalized events against detection rule criteria."""

    def __init__(self, window_counter: SlidingWindowCounter | None = None) -> None:
        self._window_counter = window_counter or SlidingWindowCounter()

    @staticmethod
    def _extract_field(event: NormalizedEvent, field_name: str) -> Any:
        """Extract a field value from event attributes or raw payload."""
        if hasattr(event, field_name):
            val = getattr(event, field_name)
            if val is not None:
                return val
        return event.raw.get(field_name)

    def _matches_condition(self, event: NormalizedEvent, condition: dict[str, Any]) -> bool:
        """Check if an event satisfies the matching condition dictionary."""
        for key, expected in condition.items():
            # Regex match
            if key.endswith("_regex"):
                field_name = key[:-6]
                val = str(self._extract_field(event, field_name) or "")
                if not re.search(str(expected), val):
                    return False
            # Numeric minimum
            elif key.startswith("min_"):
                field_name = key[4:]
                val = self._extract_field(event, field_name)
                try:
                    if val is None or float(val) < float(expected):
                        return False
                except (ValueError, TypeError):
                    return False
            # Direct Equality / Inclusion
            else:
                actual = self._extract_field(event, key)
                if actual is None:
                    return False
                # Handle enum comparisons
                actual_str = str(actual.value if hasattr(actual, "value") else actual).lower()
                expected_str = str(expected).lower()
                if actual_str != expected_str:
                    return False
        return True

    def _get_group_key(self, event: NormalizedEvent, group_by_field: str) -> str:
        """Extract grouping key value from event."""
        val = self._extract_field(event, group_by_field)
        return str(val) if val is not None else "unknown"

    async def evaluate(
        self,
        event: NormalizedEvent,
        rule: DetectionRuleConfig,
    ) -> Alert | None:
        """Evaluate an event against a single rule.

        Returns:
            Alert: If the rule triggered, otherwise None.
        """
        group_key = self._get_group_key(event, rule.group_by)
        ts = event.occurred_at.timestamp()

        # ── 1. MATCH RULE ─────────────────────────────────────────────────────
        if rule.type == RuleType.MATCH:
            if not self._matches_condition(event, rule.match):
                return None
            return Alert(
                id=uuid.uuid4(),
                rule_id=rule.id,
                title=rule.title,
                description=rule.description,
                severity=rule.severity,
                confidence=rule.confidence,
                mitre=MitreAttackMapping(
                    tactic=rule.mitre.tactic,
                    technique_id=rule.mitre.technique_id,
                    technique_name=rule.mitre.technique_name,
                ),
                playbook_category=rule.playbook_category,
                matched_event_ids=[event.event_id],
                group_by_key=group_key,
                created_at=event.ingested_at,
            )

        # ── 2. THRESHOLD RULE ─────────────────────────────────────────────────
        elif rule.type == RuleType.THRESHOLD:
            if not self._matches_condition(event, rule.match):
                return None
            redis_key = f"thresh:{rule.id}:{group_key}"
            count, matched_ids = await self._window_counter.record_and_count(
                key=redis_key,
                event_id=str(event.event_id),
                timestamp=ts,
                window_seconds=rule.window_seconds,
            )
            threshold = rule.threshold or 5
            if count >= threshold:
                return Alert(
                    id=uuid.uuid4(),
                    rule_id=rule.id,
                    title=rule.title,
                    description=f"{rule.description} (Count: {count})",
                    severity=rule.severity,
                    confidence=rule.confidence,
                    mitre=MitreAttackMapping(
                        tactic=rule.mitre.tactic,
                        technique_id=rule.mitre.technique_id,
                        technique_name=rule.mitre.technique_name,
                    ),
                    playbook_category=rule.playbook_category,
                    matched_event_ids=[uuid.UUID(eid) for eid in matched_ids],
                    group_by_key=group_key,
                    created_at=event.ingested_at,
                )

        # ── 3. DISTINCT COUNT RULE ────────────────────────────────────────────
        elif rule.type == RuleType.DISTINCT_COUNT:
            if not self._matches_condition(event, rule.match):
                return None
            distinct_field = rule.distinct_field or "dst_port"
            distinct_val = str(self._extract_field(event, distinct_field) or "")
            redis_key = f"dist:{rule.id}:{group_key}"
            count, matched_ids = await self._window_counter.record_and_count(
                key=redis_key,
                event_id=str(event.event_id),
                timestamp=ts,
                window_seconds=rule.window_seconds,
                distinct_val=distinct_val,
            )
            threshold = rule.threshold or 5
            if count >= threshold:
                return Alert(
                    id=uuid.uuid4(),
                    rule_id=rule.id,
                    title=rule.title,
                    description=f"{rule.description} (Distinct {distinct_field}: {count})",
                    severity=rule.severity,
                    confidence=rule.confidence,
                    mitre=MitreAttackMapping(
                        tactic=rule.mitre.tactic,
                        technique_id=rule.mitre.technique_id,
                        technique_name=rule.mitre.technique_name,
                    ),
                    playbook_category=rule.playbook_category,
                    matched_event_ids=[uuid.UUID(eid) for eid in matched_ids],
                    group_by_key=group_key,
                    created_at=event.ingested_at,
                )

        # ── 4. SEQUENCE RULE ──────────────────────────────────────────────────
        elif rule.type == RuleType.SEQUENCE:
            redis_key = f"seq:{rule.id}:{group_key}"
            # Check which step this event matches
            for step_idx, step_cond in enumerate(rule.sequence):
                if self._matches_condition(event, step_cond):
                    matched_ids = await self._window_counter.record_sequence_step(
                        key=redis_key,
                        step_index=step_idx,
                        event_id=str(event.event_id),
                        timestamp=ts,
                        window_seconds=rule.window_seconds,
                    )
                    # Sequence satisfied if all steps present
                    if len(matched_ids) == len(rule.sequence):
                        return Alert(
                            id=uuid.uuid4(),
                            rule_id=rule.id,
                            title=rule.title,
                            description=rule.description,
                            severity=rule.severity,
                            confidence=rule.confidence,
                            mitre=MitreAttackMapping(
                                tactic=rule.mitre.tactic,
                                technique_id=rule.mitre.technique_id,
                                technique_name=rule.mitre.technique_name,
                            ),
                            playbook_category=rule.playbook_category,
                            matched_event_ids=[uuid.UUID(eid) for eid in matched_ids],
                            group_by_key=group_key,
                            created_at=event.ingested_at,
                        )
                    break

        return None
