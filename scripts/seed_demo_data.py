"""Seed demo data — creates demo users, assets, API keys, and system settings.

Usage:
    python -m scripts.seed_demo_data

Creates:
    - Admin user (admin / admin_demo_password)
    - Analyst user (analyst / analyst_demo_password)
    - Viewer user (viewer / viewer_demo_password)
    - Sample assets with varying criticality and protection status
    - Ingestion API key
    - Initial system settings

WARNING: Demo passwords only. Never use in production.
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

# Add backend to python path for imports
backend_path = Path(__file__).resolve().parent.parent / "backend"
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

from app.config.settings import get_settings
from app.db.orm_models import ApiKeyOrm, AssetOrm, SystemSettingOrm, UserOrm
from app.db.session import Base, get_engine, get_session_factory
from app.domain.enums import AssetEnvironment, UserRole
from app.services.auth_service import hash_api_key, hash_password


async def seed_data() -> None:
    """Initialize the database tables and seed required demo data."""
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = get_session_factory()
    settings = get_settings()

    async with session_factory() as session:
        # 1. Seed Users
        users_to_seed = [
            ("admin", "admin@sentinelchain.local", "admin_demo_password", UserRole.ADMIN),
            ("analyst", "analyst@sentinelchain.local", "analyst_demo_password", UserRole.ANALYST),
            ("viewer", "viewer@sentinelchain.local", "viewer_demo_password", UserRole.VIEWER),
        ]

        for username, email, pwd, role in users_to_seed:
            existing = await session.get(UserOrm, username)  # By primary key check or query
            from sqlalchemy import select

            stmt = select(UserOrm).where(UserOrm.username == username)
            res = await session.execute(stmt)
            if not res.scalar_one_or_none():
                user = UserOrm(
                    username=username,
                    email=email,
                    password_hash=hash_password(pwd),
                    role=role,
                    is_active=True,
                )
                session.add(user)
                print(f"[+] Created user: {username} ({role.value})")

        # 2. Seed Assets
        assets_to_seed = [
            {
                "hostname": "dc-primary.corp",
                "ip_address": "10.0.0.10",
                "criticality": 5,
                "environment": AssetEnvironment.PRODUCTION,
                "is_protected": True,
                "is_internet_facing": False,
                "owner": "Infrastructure Team",
                "tags": ["domain-controller", "active-directory", "tier-0"],
            },
            {
                "hostname": "web-prod-01.corp",
                "ip_address": "192.168.1.50",
                "criticality": 4,
                "environment": AssetEnvironment.PRODUCTION,
                "is_protected": False,
                "is_internet_facing": True,
                "owner": "Web Platform Team",
                "tags": ["nginx", "customer-facing", "api-gateway"],
            },
            {
                "hostname": "db-cluster-01.corp",
                "ip_address": "10.0.0.20",
                "criticality": 5,
                "environment": AssetEnvironment.PRODUCTION,
                "is_protected": True,
                "is_internet_facing": False,
                "owner": "Data Platform",
                "tags": ["postgresql", "financial-data", "tier-0"],
            },
            {
                "hostname": "jump-host.corp",
                "ip_address": "172.16.0.10",
                "criticality": 3,
                "environment": AssetEnvironment.PRODUCTION,
                "is_protected": True,
                "is_internet_facing": False,
                "owner": "SecOps",
                "tags": ["bastion", "admin-access"],
            },
            {
                "hostname": "workstation-dev-42",
                "ip_address": "10.0.1.105",
                "criticality": 2,
                "environment": AssetEnvironment.DEVELOPMENT,
                "is_protected": False,
                "is_internet_facing": False,
                "owner": "DevOps",
                "tags": ["workstation", "developer"],
            },
        ]

        for a in assets_to_seed:
            from sqlalchemy import select

            stmt = select(AssetOrm).where(AssetOrm.hostname == a["hostname"])
            res = await session.execute(stmt)
            if not res.scalar_one_or_none():
                asset = AssetOrm(
                    hostname=a["hostname"],
                    ip_address=a["ip_address"],
                    criticality=a["criticality"],
                    environment=a["environment"],
                    is_protected=a["is_protected"],
                    is_internet_facing=a["is_internet_facing"],
                    owner=a["owner"],
                    tags=a["tags"],
                )
                session.add(asset)
                print(f"[+] Created asset: {a['hostname']} ({a['ip_address']})")

        # 3. Seed API Key
        stmt = select(ApiKeyOrm).where(ApiKeyOrm.name == "default-ingestion-key")
        res = await session.execute(stmt)
        if not res.scalar_one_or_none():
            api_key = ApiKeyOrm(
                name="default-ingestion-key",
                key_hash=hash_api_key(settings.ingestion_api_key),
                prefix=settings.ingestion_api_key[:8],
                is_active=True,
            )
            session.add(api_key)
            print(f"[+] Created ingestion API key: {settings.ingestion_api_key[:8]}...")

        # 4. Seed Autonomy Settings
        stmt = select(SystemSettingOrm).where(SystemSettingOrm.key == "autonomy_mode")
        res = await session.execute(stmt)
        if not res.scalar_one_or_none():
            setting = SystemSettingOrm(
                key="autonomy_mode",
                value=settings.default_autonomy_mode.value,
                description="Controls automatic execution of response actions",
                updated_by="system",
            )
            session.add(setting)
            print(f"[+] Set autonomy_mode: {settings.default_autonomy_mode.value}")

        await session.commit()
        print("\n[✔] Database successfully seeded with demo data!")


def main() -> None:
    """Entry point for seeding script."""
    asyncio.run(seed_data())


if __name__ == "__main__":
    main()
