"""Domain model for Protected and Managed Assets."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.domain.enums import AssetEnvironment


@dataclass(frozen=True)
class Asset:
    """Represents an IT asset (server, database, workstation) in the inventory."""

    id: UUID
    hostname: str
    ip_address: str
    criticality: int  # 1 (lowest) to 5 (mission critical)
    environment: AssetEnvironment
    is_protected: bool  # Protected assets require human approval for high-impact actions
    is_internet_facing: bool
    owner: str
    tags: list[str]
    created_at: datetime
    updated_at: datetime

    def __post_init__(self) -> None:
        """Validate criticality bounds."""
        if not 1 <= self.criticality <= 5:
            raise ValueError("Criticality must be between 1 and 5.")
