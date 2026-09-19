"""API router for Asset Inventory Management."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import require_admin, require_viewer
from app.api.schemas.asset_schemas import (
    AssetCreateRequest,
    AssetResponse,
    AssetUpdateRequest,
)
from app.api.schemas.common_schemas import PaginatedResponse
from app.db.session import get_db_session
from app.domain.user import User
from app.repositories.asset_repository import AssetRepository

router = APIRouter(prefix="/assets", tags=["Assets"])


@router.get("", response_model=PaginatedResponse[AssetResponse])
@router.get("/", response_model=PaginatedResponse[AssetResponse], include_in_schema=False)
async def list_assets(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[User, Depends(require_viewer)],
    criticality: int | None = Query(None, ge=1, le=5),
    is_protected: bool | None = Query(None),
    is_internet_facing: bool | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> PaginatedResponse[AssetResponse]:
    """List managed assets with optional filtering."""
    repo = AssetRepository(session)
    assets, total = await repo.list_assets(
        criticality=criticality,
        is_protected=is_protected,
        is_internet_facing=is_internet_facing,
        limit=limit,
        offset=offset,
    )
    items = [
        AssetResponse(
            id=a.id,
            hostname=a.hostname,
            ip_address=a.ip_address,
            criticality=a.criticality,
            environment=a.environment,
            is_protected=a.is_protected,
            is_internet_facing=a.is_internet_facing,
            owner=a.owner,
            tags=a.tags,
            created_at=a.created_at,
            updated_at=a.updated_at,
        )
        for a in assets
    ]
    return PaginatedResponse(items=items, total=total, limit=limit, offset=offset)


@router.get("/{asset_id}", response_model=AssetResponse)
async def get_asset(
    asset_id: UUID,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[User, Depends(require_viewer)],
) -> AssetResponse:
    """Retrieve an asset by ID."""
    repo = AssetRepository(session)
    asset = await repo.get_by_id(asset_id)
    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "ASSET_NOT_FOUND", "message": f"Asset '{asset_id}' not found"}},
        )
    return AssetResponse(
        id=asset.id,
        hostname=asset.hostname,
        ip_address=asset.ip_address,
        criticality=asset.criticality,
        environment=asset.environment,
        is_protected=asset.is_protected,
        is_internet_facing=asset.is_internet_facing,
        owner=asset.owner,
        tags=asset.tags,
        created_at=asset.created_at,
        updated_at=asset.updated_at,
    )


@router.post("", response_model=AssetResponse, status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=AssetResponse, status_code=status.HTTP_201_CREATED, include_in_schema=False)
async def create_asset(
    payload: AssetCreateRequest,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[User, Depends(require_admin)],
) -> AssetResponse:
    """Create a new managed asset (Admin only)."""
    repo = AssetRepository(session)
    existing = await repo.get_by_hostname(payload.hostname)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"error": {"code": "ASSET_EXISTS", "message": f"Asset with hostname '{payload.hostname}' already exists"}},
        )

    asset = await repo.create(
        hostname=payload.hostname,
        ip_address=payload.ip_address,
        criticality=payload.criticality,
        environment=payload.environment,
        is_protected=payload.is_protected,
        is_internet_facing=payload.is_internet_facing,
        owner=payload.owner,
        tags=payload.tags,
    )
    return AssetResponse(
        id=asset.id,
        hostname=asset.hostname,
        ip_address=asset.ip_address,
        criticality=asset.criticality,
        environment=asset.environment,
        is_protected=asset.is_protected,
        is_internet_facing=asset.is_internet_facing,
        owner=asset.owner,
        tags=asset.tags,
        created_at=asset.created_at,
        updated_at=asset.updated_at,
    )


@router.put("/{asset_id}", response_model=AssetResponse)
async def update_asset(
    asset_id: UUID,
    payload: AssetUpdateRequest,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[User, Depends(require_admin)],
) -> AssetResponse:
    """Update asset attributes (Admin only)."""
    repo = AssetRepository(session)
    asset = await repo.update(
        asset_id=asset_id,
        criticality=payload.criticality,
        environment=payload.environment,
        is_protected=payload.is_protected,
        is_internet_facing=payload.is_internet_facing,
        owner=payload.owner,
        tags=payload.tags,
    )
    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "ASSET_NOT_FOUND", "message": f"Asset '{asset_id}' not found"}},
        )
    return AssetResponse(
        id=asset.id,
        hostname=asset.hostname,
        ip_address=asset.ip_address,
        criticality=asset.criticality,
        environment=asset.environment,
        is_protected=asset.is_protected,
        is_internet_facing=asset.is_internet_facing,
        owner=asset.owner,
        tags=asset.tags,
        created_at=asset.created_at,
        updated_at=asset.updated_at,
    )


@router.delete("/{asset_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_asset(
    asset_id: UUID,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[User, Depends(require_admin)],
) -> None:
    """Delete an asset (Admin only)."""
    repo = AssetRepository(session)
    deleted = await repo.delete(asset_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "ASSET_NOT_FOUND", "message": f"Asset '{asset_id}' not found"}},
        )
