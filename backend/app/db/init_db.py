"""Database table initialization and default seed data loader.

Ensures all tables exist on startup and seeds demo users, default assets,
and baseline system settings if the database is freshly provisioned.
"""

from __future__ import annotations

from datetime import datetime, timezone
import uuid

from sqlalchemy import select
import structlog

from app.db.orm_models import (
    ApiKeyOrm,
    AssetOrm,
    Base,
    SystemSettingOrm,
    UserOrm,
)
from app.db.session import get_engine, get_session_factory
from app.domain.enums import AssetEnvironment, UserRole
from app.services.auth_service import hash_api_key, hash_password

logger = structlog.get_logger(__name__)


async def init_database() -> None:
    """Create all ORM tables and seed default baseline demo data."""
    engine = get_engine()

    try:
        # Create tables
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    except Exception as exc:
        logger.warning("primary_database_unavailable_falling_back_to_sqlite", error=str(exc))
        from app.config.settings import get_settings
        import app.db.session as session_mod

        settings = get_settings()
        settings.database_url = "sqlite+aiosqlite:///sentinelchain.db"
        session_mod._engine = None
        session_mod._session_factory = None
        engine = session_mod.get_engine()

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    session_factory = get_session_factory()
    async with session_factory() as session:
        # 1. Seed demo users
        user_stmt = select(UserOrm).limit(1)
        result = await session.execute(user_stmt)
        existing_user = result.scalar_one_or_none()

        if not existing_user:
            logger.info("seeding_default_users")
            users = [
                UserOrm(
                    id=uuid.uuid4(),
                    username="admin",
                    email="admin@sentinelchain.io",
                    password_hash=hash_password("admin_demo_password"),
                    role=UserRole.ADMIN,
                    is_active=True,
                ),
                UserOrm(
                    id=uuid.uuid4(),
                    username="analyst",
                    email="analyst@sentinelchain.io",
                    password_hash=hash_password("analyst_demo_password"),
                    role=UserRole.ANALYST,
                    is_active=True,
                ),
                UserOrm(
                    id=uuid.uuid4(),
                    username="viewer",
                    email="viewer@sentinelchain.io",
                    password_hash=hash_password("viewer_demo_password"),
                    role=UserRole.VIEWER,
                    is_active=True,
                ),
            ]
            session.add_all(users)

        # 2. Seed default Ingestion API Key
        key_stmt = select(ApiKeyOrm).limit(1)
        key_res = await session.execute(key_stmt)
        existing_key = key_res.scalar_one_or_none()

        if not existing_key:
            logger.info("seeding_default_api_key")
            api_key = ApiKeyOrm(
                id=uuid.uuid4(),
                name="Default Ingestion API Key",
                key_hash=hash_api_key("sentinelchain-demo-api-key"),
                prefix="sentinel",
                is_active=True,
            )
            session.add(api_key)

        # 3. Seed default managed assets
        asset_stmt = select(AssetOrm).limit(1)
        asset_res = await session.execute(asset_stmt)
        existing_asset = asset_res.scalar_one_or_none()

        if not existing_asset:
            logger.info("seeding_default_assets")
            assets = [
                AssetOrm(
                    id=uuid.uuid4(),
                    hostname="app-prod-01.corp",
                    ip_address="10.0.0.50",
                    criticality=4,
                    environment=AssetEnvironment.PRODUCTION,
                    is_protected=True,
                    is_internet_facing=True,
                    owner="AppSec Team",
                    tags=["web", "production", "internet-facing"],
                ),
                AssetOrm(
                    id=uuid.uuid4(),
                    hostname="dc-primary.corp",
                    ip_address="10.0.0.10",
                    criticality=5,
                    environment=AssetEnvironment.PRODUCTION,
                    is_protected=True,
                    is_internet_facing=False,
                    owner="InfraSec",
                    tags=["domain-controller", "tier-0", "protected"],
                ),
                AssetOrm(
                    id=uuid.uuid4(),
                    hostname="web-gateway-01.dmz",
                    ip_address="192.168.1.100",
                    criticality=3,
                    environment=AssetEnvironment.PRODUCTION,
                    is_protected=False,
                    is_internet_facing=True,
                    owner="Network Ops",
                    tags=["gateway", "dmz", "edge"],
                ),
                AssetOrm(
                    id=uuid.uuid4(),
                    hostname="db-cluster-01.internal",
                    ip_address="10.0.0.20",
                    criticality=5,
                    environment=AssetEnvironment.PRODUCTION,
                    is_protected=True,
                    is_internet_facing=False,
                    owner="Data Ops",
                    tags=["database", "postgresql", "tier-0"],
                ),
                AssetOrm(
                    id=uuid.uuid4(),
                    hostname="workstation-eng-42.corp",
                    ip_address="10.0.1.42",
                    criticality=2,
                    environment=AssetEnvironment.INTERNAL,
                    is_protected=False,
                    is_internet_facing=False,
                    owner="Engineering",
                    tags=["workstation", "internal"],
                ),
            ]
            session.add_all(assets)

        # 4. Seed default system settings (Autonomy Mode)
        mode_stmt = select(SystemSettingOrm).where(SystemSettingOrm.key == "autonomy_mode")
        mode_res = await session.execute(mode_stmt)
        existing_mode = mode_res.scalar_one_or_none()

        if not existing_mode:
            logger.info("seeding_default_system_settings")
            setting = SystemSettingOrm(
                key="autonomy_mode",
                value="auto",
                description="System runtime autonomy mode: auto | approval_required | recommend_only | off",
                updated_by="system",
                updated_at=datetime.now(timezone.utc),
            )
            session.add(setting)

        await session.commit()
