"""API router for System Settings and Playbooks."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import require_admin, require_viewer
from app.config.settings import AutonomyMode, get_settings
from app.db.orm_models import SystemSettingOrm
from app.db.session import get_db_session
from app.domain.enums import EntryType
from app.domain.user import User
from app.services.integrity.hash_chain_ledger import HashChainLedger
from app.services.response.playbook_loader import PlaybookLoader

router = APIRouter(prefix="/settings", tags=["System Settings"])


class AutonomyModeUpdateRequest(BaseModel):
    """Payload to update runtime autonomy mode."""

    autonomy_mode: AutonomyMode


class AutonomyModeResponse(BaseModel):
    """Current system autonomy mode."""

    autonomy_mode: AutonomyMode
    updated_by: str
    description: str


@router.get("/autonomy-mode", response_model=AutonomyModeResponse)
async def get_autonomy_mode(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[User, Depends(require_viewer)],
) -> AutonomyModeResponse:
    """Retrieve the current system autonomy mode."""
    settings = get_settings()
    stmt = select(SystemSettingOrm).where(SystemSettingOrm.key == "autonomy_mode")
    res = await session.execute(stmt)
    setting = res.scalar_one_or_none()

    if setting:
        return AutonomyModeResponse(
            autonomy_mode=AutonomyMode(setting.value),
            updated_by=setting.updated_by,
            description=setting.description,
        )

    return AutonomyModeResponse(
        autonomy_mode=settings.default_autonomy_mode,
        updated_by="system",
        description="Default system autonomy setting",
    )


@router.put("/autonomy-mode", response_model=AutonomyModeResponse)
async def update_autonomy_mode(
    payload: AutonomyModeUpdateRequest,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_admin)],
) -> AutonomyModeResponse:
    """Update runtime autonomy mode (Admin only)."""
    stmt = select(SystemSettingOrm).where(SystemSettingOrm.key == "autonomy_mode")
    res = await session.execute(stmt)
    setting = res.scalar_one_or_none()

    old_mode = setting.value if setting else "unknown"

    if setting:
        setting.value = payload.autonomy_mode.value
        setting.updated_by = current_user.username
    else:
        setting = SystemSettingOrm(
            key="autonomy_mode",
            value=payload.autonomy_mode.value,
            description="Controls automatic execution of response actions",
            updated_by=current_user.username,
        )
        session.add(setting)

    await session.flush()

    # Append AUTONOMY_MODE_CHANGED to cryptographic ledger
    ledger = HashChainLedger(session)
    await ledger.append_entry(
        entry_type=EntryType.AUTONOMY_MODE_CHANGED,
        payload={
            "old_mode": old_mode,
            "new_mode": payload.autonomy_mode.value,
            "changed_by": current_user.username,
        },
    )

    return AutonomyModeResponse(
        autonomy_mode=payload.autonomy_mode,
        updated_by=current_user.username,
        description="Controls automatic execution of response actions",
    )


@router.get("/playbooks")
async def list_playbooks(
    _: Annotated[User, Depends(require_viewer)],
) -> list[dict[str, Any]]:
    """Retrieve all loaded response playbooks."""
    from pathlib import Path

    pb_dir = Path(__file__).resolve().parent.parent.parent.parent / "playbooks"
    if not pb_dir.exists():
        pb_dir = Path(__file__).resolve().parents[2] / "backend" / "playbooks"
    loaded = PlaybookLoader.load_from_directory(pb_dir)
    return [p.model_dump() for p in loaded]
