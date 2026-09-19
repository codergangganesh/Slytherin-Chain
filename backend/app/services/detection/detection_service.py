"""Detection service coordinating rule evaluation and alert generation."""

from __future__ import annotations

from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.alert import Alert
from app.domain.normalized_event import NormalizedEvent
from app.repositories.alert_repository import AlertRepository
from app.services.detection.rule_evaluator import RuleEvaluator
from app.services.detection.rule_loader import DetectionRuleConfig, RuleLoader


class DetectionService:
    """Evaluates security events against loaded detection rules and persists unsuppressed alerts."""

    def __init__(
        self,
        rules: list[DetectionRuleConfig] | None = None,
        rules_directory: Path | None = None,
        evaluator: RuleEvaluator | None = None,
    ) -> None:
        self._evaluator = evaluator or RuleEvaluator()
        if rules is not None:
            self._rules = rules
        else:
            default_dir = (
                rules_directory or Path(__file__).resolve().parent.parent.parent.parent / "rules"
            )
            self._rules = RuleLoader.load_rules_from_directory(default_dir)

    @property
    def rules(self) -> list[DetectionRuleConfig]:
        """Return the list of loaded detection rules."""
        return self._rules

    async def process_event(
        self,
        event: NormalizedEvent,
        session: AsyncSession,
    ) -> list[Alert]:
        """Evaluate an event across all rules, saving and returning any new alerts.

        Args:
            event: The normalized event to inspect.
            session: Active database session for alert storage and suppression checking.

        Returns:
            list[Alert]: Newly created, unsuppressed alerts.
        """
        alert_repo = AlertRepository(session)
        new_alerts: list[Alert] = []

        for rule in self._rules:
            alert = await self._evaluator.evaluate(event, rule)
            if alert is None:
                continue

            # Check suppression window
            is_suppressed = await alert_repo.is_suppressed(
                rule_id=alert.rule_id,
                group_by_key=alert.group_by_key,
                suppress_seconds=rule.suppress_for_seconds,
            )
            if is_suppressed:
                continue

            # Persist alert
            saved_alert = await alert_repo.save(alert)
            new_alerts.append(saved_alert)

        return new_alerts
