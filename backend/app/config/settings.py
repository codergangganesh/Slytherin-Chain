"""Application configuration loaded from environment variables.

Uses pydantic-settings to provide typed, validated configuration.
All settings have sensible defaults for local development.
See .env.example for full documentation of each variable.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic_settings import BaseSettings, SettingsConfigDict


class AppEnvironment(StrEnum):
    """Application environment identifiers."""

    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"


class AutonomyMode(StrEnum):
    """Controls how the response engine operates.

    - off: no automatic actions
    - recommend_only: proposes actions, human executes
    - approval_required: human approves everything
    - auto: auto-run when all guardrails pass
    """

    OFF = "off"
    RECOMMEND_ONLY = "recommend_only"
    APPROVAL_REQUIRED = "approval_required"
    AUTO = "auto"


class Settings(BaseSettings):
    """Central configuration for the SentinelChain backend.

    Values are loaded from environment variables (and .env files).
    Every setting has a default suitable for local development.
    """

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ───────────────────────────────────────────────────────
    app_env: AppEnvironment = AppEnvironment.DEVELOPMENT
    secret_key: str = "sentinelchain-dev-secret-change-in-production"
    access_token_expire_minutes: int = 30
    refresh_token_expire_minutes: int = 10080
    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    # ── Database ──────────────────────────────────────────────────────────
    database_url: str = "sqlite+aiosqlite:///sentinelchain.db"

    # ── Redis ─────────────────────────────────────────────────────────────
    redis_url: str = "redis://localhost:6379/0"
    redis_stream_events: str = "events.normalized"
    redis_consumer_group: str = "detection_workers"

    # ── MinIO ─────────────────────────────────────────────────────────────
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "sentinelchain"
    minio_secret_key: str = "sentinelchain_dev_password"
    minio_bucket_evidence: str = "evidence"
    minio_bucket_reports: str = "reports"
    minio_use_ssl: bool = False

    # ── Blockchain / Integrity ────────────────────────────────────────────
    anchor_chain_rpc_url: str = "http://localhost:8545"
    anchor_chain_id: int = 31337
    anchor_contract_address: str = ""
    anchor_wallet_private_key: str = (
        "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"
    )
    anchor_confirmations: int = 1
    anchor_interval_seconds: int = 300

    # ── Autonomous Response ───────────────────────────────────────────────
    default_autonomy_mode: AutonomyMode = AutonomyMode.AUTO
    enable_real_enforcement: bool = False
    max_auto_actions_per_hour_global: int = 50
    max_auto_actions_per_hour_per_target_type: int = 20
    allowlisted_ips: str = "10.0.0.1,192.168.1.1,172.16.0.1"

    # ── Enrichment ────────────────────────────────────────────────────────
    abuseipdb_api_key: str = ""
    threat_intel_cache_ttl_seconds: int = 3600

    # ── Risk Scoring Weights ──────────────────────────────────────────────
    risk_weight_severity: float = 0.30
    risk_weight_confidence: float = 0.20
    risk_weight_asset: float = 0.25
    risk_weight_exposure: float = 0.10
    risk_weight_intel: float = 0.15

    # ── Detection ─────────────────────────────────────────────────────────
    correlation_window_seconds: int = 1800

    # ── Reporting ─────────────────────────────────────────────────────────
    enable_llm_summary: bool = False
    llm_provider: str = "openai"
    llm_api_key: str = ""
    llm_model: str = "gpt-4o-mini"

    # ── Notifications ─────────────────────────────────────────────────────
    notification_webhook_url: str = ""

    # ── Ingestion ─────────────────────────────────────────────────────────
    max_batch_size: int = 500
    ingestion_api_key: str = "sentinelchain-demo-api-key"

    # ── Logging ───────────────────────────────────────────────────────────
    log_level: str = "INFO"
    log_format: str = "json"

    @property
    def cors_origin_list(self) -> list[str]:
        """Parse comma-separated CORS origins into a list."""
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def allowlisted_ip_list(self) -> list[str]:
        """Parse comma-separated allowlisted IPs into a list."""
        return [ip.strip() for ip in self.allowlisted_ips.split(",") if ip.strip()]


def get_settings() -> Settings:
    """Create and return the application settings instance.

    Returns:
        Settings: Validated configuration loaded from environment.
    """
    return Settings()
