"""Abstract enforcement connector interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any
from uuid import UUID

from app.domain.enums import ActionType


class EnforcementConnector(ABC):
    """Abstract interface defining the execution lifecycle for an enforcement target."""

    @abstractmethod
    def supports_action(self, action_type: ActionType) -> bool:
        """Check if this connector supports the given action type."""
        pass

    @abstractmethod
    async def validate(self, target: str, parameters: dict[str, Any]) -> tuple[bool, str]:
        """Pre-execution syntax and parameter validation."""
        pass

    @abstractmethod
    async def dry_run(self, target: str, parameters: dict[str, Any]) -> dict[str, Any]:
        """Simulate execution and return anticipated effects without mutating state."""
        pass

    @abstractmethod
    async def execute(
        self,
        action_id: UUID,
        incident_id: UUID,
        target: str,
        parameters: dict[str, Any],
        ttl_seconds: int | None = None,
    ) -> dict[str, Any]:
        """Perform real or simulated enforcement action."""
        pass

    @abstractmethod
    async def rollback(
        self,
        action_id: UUID,
        target: str,
        parameters: dict[str, Any],
    ) -> dict[str, Any]:
        """Revert a previously executed action."""
        pass
