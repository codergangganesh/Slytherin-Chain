"""FastAPI application factory and router registration.

Creates the SentinelChain API application with middleware, CORS,
health endpoints, and all routers registered under /api/v1.
"""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from typing import Any, AsyncGenerator

# Ensure repository root is in sys.path
_ROOT_DIR = str(Path(__file__).resolve().parents[2])
if _ROOT_DIR not in sys.path:
    sys.path.insert(0, _ROOT_DIR)

import structlog
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.api.routers import (
    assets_router,
    auth_router,
    dashboard_router,
    events_router,
    incidents_router,
    integrity_router,
    reports_router,
    response_actions_router,
    settings_router,
    simulator_router,
)
from app.config.logging_config import (
    configure_logging,
    get_correlation_id,
    set_correlation_id,
)
from app.config.settings import get_settings

logger = structlog.get_logger(__name__)

# ── Application metadata ─────────────────────────────────────────────────────

APP_TITLE = "SentinelChain"
APP_DESCRIPTION = (
    "Autonomous Response & Incident Management Platform — "
    "Detects threats, responds autonomously under guardrails, tracks incidents, "
    "generates reports, and anchors tamper-evident integrity proofs on a blockchain."
)
APP_VERSION = "0.1.0"


# ── Middleware ────────────────────────────────────────────────────────────────


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """Injects or propagates a correlation ID through every request."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        """Process the request, attaching a correlation ID."""
        incoming_id = request.headers.get("X-Correlation-ID", "")
        if incoming_id:
            set_correlation_id(incoming_id)
        else:
            set_correlation_id("")
            incoming_id = get_correlation_id()

        response = await call_next(request)
        response.headers["X-Correlation-ID"] = incoming_id
        return response


# ── Active WebSocket connection manager ───────────────────────────────────────


class ConnectionManager:
    """Manages active WebSocket connections for live feed."""

    def __init__(self) -> None:
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict[str, Any]) -> None:
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except Exception:
                pass


ws_manager = ConnectionManager()


# ── Lifespan ──────────────────────────────────────────────────────────────────


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler for startup and shutdown events."""
    settings = get_settings()
    configure_logging(log_level=settings.log_level, log_format=settings.log_format)

    logger.info(
        "sentinelchain_starting",
        version=APP_VERSION,
        environment=settings.app_env,
    )

    # Initialize database tables and seed initial baseline demo data
    try:
        from app.db.init_db import init_database

        await init_database()
        logger.info("database_initialized_and_seeded")
    except Exception as exc:
        logger.error("database_init_error", error=str(exc))

    yield

    logger.info("sentinelchain_shutting_down")


# ── Health endpoints ──────────────────────────────────────────────────────────


def _build_health_response() -> dict[str, Any]:
    return {
        "status": "ok",
        "service": APP_TITLE,
        "version": APP_VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


async def _check_dependency_health(settings: Any) -> dict[str, Any]:
    checks: dict[str, dict[str, str]] = {}

    # PostgreSQL
    try:
        from sqlalchemy import text
        from sqlalchemy.ext.asyncio import create_async_engine

        engine = create_async_engine(settings.database_url, pool_pre_ping=True)
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        await engine.dispose()
        checks["postgres"] = {"status": "ok"}
    except Exception as exc:
        checks["postgres"] = {"status": "error", "message": str(exc)}

    # Redis
    try:
        import redis.asyncio as aioredis

        redis_client = aioredis.from_url(
            settings.redis_url,
            socket_connect_timeout=0.2,
            socket_timeout=0.2,
        )
        await asyncio.wait_for(redis_client.ping(), timeout=0.3)
        await redis_client.aclose()
        checks["redis"] = {"status": "ok"}
    except Exception as exc:
        checks["redis"] = {"status": "error", "message": str(exc)}

    # MinIO
    try:
        from minio import Minio
        import urllib3

        http_client = urllib3.PoolManager(timeout=urllib3.Timeout(connect=0.2, read=0.3))
        minio_client = Minio(
            settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=settings.minio_use_ssl,
            http_client=http_client,
        )
        minio_client.list_buckets()
        checks["minio"] = {"status": "ok"}
    except Exception as exc:
        checks["minio"] = {"status": "error", "message": str(exc)}

    # Blockchain (Anvil / Sepolia)
    try:
        from web3 import Web3

        w3 = Web3(Web3.HTTPProvider(settings.anchor_chain_rpc_url, request_kwargs={"timeout": 0.3}))
        if w3.is_connected():
            checks["blockchain"] = {"status": "ok", "chain_id": str(w3.eth.chain_id)}
        else:
            checks["blockchain"] = {"status": "error", "message": "not connected"}
    except Exception as exc:
        checks["blockchain"] = {"status": "error", "message": str(exc)}

    all_ok = all(c["status"] == "ok" for c in checks.values())
    return {
        "status": "ok" if all_ok else "degraded",
        "service": APP_TITLE,
        "version": APP_VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "checks": checks,
    }


# ── App factory ───────────────────────────────────────────────────────────────


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title=APP_TITLE,
        description=APP_DESCRIPTION,
        version=APP_VERSION,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    # ── CORS ──────────────────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:8000",
            "http://127.0.0.1:8000",
            *settings.cors_origin_list,
        ],
        allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Correlation-ID"],
    )

    # ── Correlation ID middleware ─────────────────────────────────────────
    app.add_middleware(CorrelationIdMiddleware)

    # ── Root and Health endpoints ─────────────────────────────────────────

    @app.get(
        "/",
        tags=["Root"],
        summary="Root landing redirect to API documentation",
        include_in_schema=False,
    )
    async def root() -> RedirectResponse:
        return RedirectResponse(url="/docs")

    @app.get(
        "/health",
        tags=["Health"],
        summary="Liveness probe",
        response_class=JSONResponse,
    )
    async def health() -> dict[str, Any]:
        return _build_health_response()

    @app.get(
        "/ready",
        tags=["Health"],
        summary="Readiness probe",
        response_class=JSONResponse,
    )
    async def ready() -> dict[str, Any]:
        return await _check_dependency_health(settings)

    # ── WebSocket Live feed ───────────────────────────────────────────────

    @app.websocket("/ws/live")
    async def websocket_live_endpoint(websocket: WebSocket) -> None:
        await ws_manager.connect(websocket)
        try:
            while True:
                # Keep alive ping-pong
                data = await websocket.receive_text()
                if data == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))
        except WebSocketDisconnect:
            ws_manager.disconnect(websocket)

    # ── API routers (registered under /api/v1) ────────────────────────────
    app.include_router(auth_router.router, prefix="/api/v1")
    app.include_router(events_router.router, prefix="/api/v1")
    app.include_router(incidents_router.router, prefix="/api/v1")
    app.include_router(assets_router.router, prefix="/api/v1")
    app.include_router(response_actions_router.router, prefix="/api/v1")
    app.include_router(integrity_router.router, prefix="/api/v1")
    app.include_router(reports_router.router, prefix="/api/v1")
    app.include_router(dashboard_router.router, prefix="/api/v1")
    app.include_router(settings_router.router, prefix="/api/v1")
    app.include_router(simulator_router.router, prefix="/api/v1")

    # Direct top-level alias for playbooks
    @app.get("/api/v1/playbooks", tags=["Playbooks"], include_in_schema=False)
    async def playbooks_alias() -> list[dict[str, Any]]:
        from app.services.response.playbook_loader import PlaybookLoader
        from pathlib import Path

        pb_dir = Path(__file__).resolve().parent.parent / "playbooks"
        loaded = PlaybookLoader.load_from_directory(pb_dir)
        return [p.model_dump() for p in loaded]

    return app
