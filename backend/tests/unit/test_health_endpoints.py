"""Tests for health endpoints.

Verifies that /health and /ready endpoints respond correctly
as part of the Phase 0 acceptance criteria.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import create_app


class TestHealthEndpoints:
    """Tests for liveness and readiness probes."""

    def test_health_returns_ok(self) -> None:
        """Health endpoint returns 200 with status ok."""
        client = TestClient(create_app())
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "SentinelChain"
        assert "version" in data
        assert "timestamp" in data

    def test_health_contains_version(self) -> None:
        """Health endpoint includes the application version."""
        client = TestClient(create_app())
        response = client.get("/health")

        data = response.json()
        assert data["version"] == "0.1.0"

    def test_ready_returns_response(self) -> None:
        """Ready endpoint returns a response (may be degraded without deps).

        In CI without PostgreSQL/Redis/MinIO/Anvil, individual checks
        may fail but the endpoint itself must respond with 200.
        """
        client = TestClient(create_app())
        response = client.get("/ready")

        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "SentinelChain"
        assert "checks" in data
        assert "status" in data

    def test_correlation_id_header_propagated(self) -> None:
        """Requests with X-Correlation-ID get the same ID back in the response."""
        client = TestClient(create_app())
        test_id = "test-correlation-12345"
        response = client.get("/health", headers={"X-Correlation-ID": test_id})

        assert response.status_code == 200
        assert response.headers.get("X-Correlation-ID") == test_id

    def test_correlation_id_generated_when_missing(self) -> None:
        """Requests without X-Correlation-ID get a generated one in the response."""
        client = TestClient(create_app())
        response = client.get("/health")

        assert response.status_code == 200
        correlation_id = response.headers.get("X-Correlation-ID")
        assert correlation_id is not None
        assert len(correlation_id) > 0
