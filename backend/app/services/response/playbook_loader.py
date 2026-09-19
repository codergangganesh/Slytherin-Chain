"""Playbook loader and validation for YAML response policies."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from pydantic import BaseModel, Field, field_validator
import yaml

from app.config.settings import AutonomyMode
from app.domain.enums import ActionType
from app.domain.exceptions import PlaybookValidationError


class ActionApprovalConditions(BaseModel):
    """Conditions under which an automated action must escalate to human approval."""

    asset_criticality_at_least: int | None = Field(default=None, ge=1, le=5)
    is_protected_asset: bool | None = None
    target_role_is_privileged: bool | None = None


class PlaybookActionConfig(BaseModel):
    """Specification for a discrete action within a playbook."""

    action_type: ActionType
    target: str
    ttl_seconds: int | None = Field(default=None, ge=60)
    requires_approval_if: ActionApprovalConditions | None = None

    @field_validator("action_type", mode="before")
    @classmethod
    def parse_action_type(cls, val: Any) -> ActionType:
        if isinstance(val, ActionType):
            return val
        return ActionType(str(val).lower())


class PlaybookConditions(BaseModel):
    """Trigger conditions for playbook invocation."""

    min_risk_score: float = Field(default=0.0, ge=0.0, le=100.0)
    min_confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class ResponsePlaybookConfig(BaseModel):
    """Pydantic validated model for a response playbook."""

    id: str
    applies_to_category: str
    autonomy_mode_required: AutonomyMode = AutonomyMode.AUTO
    conditions: PlaybookConditions = Field(default_factory=PlaybookConditions)
    actions: list[PlaybookActionConfig] = Field(default_factory=list)


class PlaybookLoader:
    """Loads and validates response playbooks from YAML files."""

    @classmethod
    def load_from_file(cls, file_path: Path) -> ResponsePlaybookConfig:
        """Parse a single playbook file."""
        try:
            with open(file_path, encoding="utf-8") as f:
                data = yaml.safe_load(f)
            return ResponsePlaybookConfig(**data)
        except Exception as err:
            raise PlaybookValidationError(str(file_path.name), str(err)) from err

    @classmethod
    def load_from_directory(cls, dir_path: Path) -> list[ResponsePlaybookConfig]:
        """Load all playbooks from directory."""
        playbooks: list[ResponsePlaybookConfig] = []
        if not dir_path.exists():
            return playbooks

        for path in sorted(dir_path.glob("*.yaml")):
            playbooks.append(cls.load_from_file(path))
        for path in sorted(dir_path.glob("*.yml")):
            playbooks.append(cls.load_from_file(path))

        return playbooks
