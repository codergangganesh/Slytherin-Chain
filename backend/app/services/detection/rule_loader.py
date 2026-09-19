"""Rule loader and schema validation for YAML detection rules."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from pydantic import BaseModel, Field, field_validator
import yaml

from app.domain.enums import RuleType
from app.domain.exceptions import RuleValidationError


class MitreConfig(BaseModel):
    """MITRE ATT&CK schema."""

    tactic: str
    technique_id: str
    technique_name: str


class DetectionRuleConfig(BaseModel):
    """Pydantic validated model for a detection rule."""

    id: str
    title: str
    description: str
    type: RuleType
    severity: float = Field(..., ge=0.0, le=1.0)
    confidence: float = Field(..., ge=0.0, le=1.0)
    match: dict[str, Any] = Field(default_factory=dict)
    sequence: list[dict[str, Any]] = Field(default_factory=list)
    group_by: str
    distinct_field: str | None = None
    threshold: int | None = None
    window_seconds: int = 120
    mitre: MitreConfig
    playbook_category: str
    suppress_for_seconds: int = 300

    @field_validator("type", mode="before")
    @classmethod
    def parse_rule_type(cls, val: Any) -> RuleType:
        if isinstance(val, RuleType):
            return val
        return RuleType(str(val).lower())


class RuleLoader:
    """Loads and validates detection rules from disk directory."""

    @classmethod
    def load_rule_from_file(cls, file_path: Path) -> DetectionRuleConfig:
        """Parse a single YAML rule file."""
        try:
            with open(file_path, encoding="utf-8") as f:
                data = yaml.safe_load(f)
            return DetectionRuleConfig(**data)
        except Exception as err:
            raise RuleValidationError(str(file_path.name), str(err)) from err

    @classmethod
    def load_rules_from_directory(cls, dir_path: Path) -> list[DetectionRuleConfig]:
        """Load all YAML detection rules from a directory."""
        rules: list[DetectionRuleConfig] = []
        if not dir_path.exists():
            return rules

        for path in sorted(dir_path.glob("*.yaml")):
            rule = cls.load_rule_from_file(path)
            rules.append(rule)
        for path in sorted(dir_path.glob("*.yml")):
            rule = cls.load_rule_from_file(path)
            rules.append(rule)

        return rules
