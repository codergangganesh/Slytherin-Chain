"""Shared test fixtures for the SentinelChain backend test suite.

Provides common fixtures for database sessions, HTTP clients, and test data
that are reused across unit and integration tests.
"""

from __future__ import annotations

from typing import AsyncGenerator

import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture
def app_client() -> TestClient:
    """Create a FastAPI test client for endpoint testing.

    Returns:
        TestClient: A synchronous test client wrapping the application.
    """
    app = create_app()
    return TestClient(app)
