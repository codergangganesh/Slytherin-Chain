"""Offline threat intelligence provider reading from local seed JSON dataset."""

from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class IntelReputation:
    """Reputation score and categorization tags for an IP or hash."""

    target: str
    reputation_score: float  # 0.0 (clean) to 1.0 (malicious)
    tags: list[str] = field(default_factory=list)
    threat_name: str | None = None


class OfflineThreatIntelProvider:
    """Provides threat intelligence reputation lookups from offline seed dataset."""

    def __init__(self, data_file: Path | None = None) -> None:
        self._data_file = (
            data_file
            or Path(__file__).resolve().parent.parent.parent.parent / "data" / "offline_threat_intel.json"
        )
        self._data: dict[str, Any] = self._load_data()

    def _load_data(self) -> dict[str, Any]:
        """Load JSON dataset from disk."""
        if not self._data_file.exists():
            return {"ips": {}, "file_hashes": {}}
        try:
            with open(self._data_file, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {"ips": {}, "file_hashes": {}}

    def lookup_ip(self, ip_address: str) -> IntelReputation:
        """Lookup reputation for an IP address."""
        ip_data = self._data.get("ips", {}).get(ip_address)
        if ip_data:
            return IntelReputation(
                target=ip_address,
                reputation_score=float(ip_data.get("reputation_score", 0.0)),
                tags=list(ip_data.get("tags", [])),
            )
        # Default benign / unknown
        return IntelReputation(target=ip_address, reputation_score=0.1, tags=["unknown-ip"])

    def lookup_file_hash(self, file_hash: str) -> IntelReputation:
        """Lookup reputation for a SHA-256 file hash."""
        hash_data = self._data.get("file_hashes", {}).get(file_hash.lower())
        if hash_data:
            return IntelReputation(
                target=file_hash,
                reputation_score=float(hash_data.get("reputation_score", 0.0)),
                tags=list(hash_data.get("tags", [])),
                threat_name=hash_data.get("threat_name"),
            )
        return IntelReputation(target=file_hash, reputation_score=0.1, tags=["unknown-hash"])
