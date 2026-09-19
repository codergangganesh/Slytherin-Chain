"""API router for Incident Report generation and downloads."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
from typing import Annotated
from uuid import UUID
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.object_storage.minio_object_store import MinioObjectStore
from app.api.dependencies import require_viewer
from app.db.orm_models import ReportOrm
from app.db.session import get_db_session
from app.domain.enums import EntryType
from app.domain.user import User
from app.services.integrity.hash_chain_ledger import HashChainLedger
from app.services.reporting.incident_report_builder import IncidentReportBuilder
from app.services.reporting.report_renderers import ReportRenderers

router = APIRouter(prefix="/reports", tags=["Incident Reports"])


class GenerateReportResponse(BaseModel):
    """Result of generating an incident report."""

    report_id: UUID
    incident_id: UUID
    format: str
    file_hash_sha256: str
    file_size_bytes: int
    created_at: datetime
    download_url: str


@router.post("/incidents/{incident_id}", response_model=GenerateReportResponse, status_code=status.HTTP_201_CREATED)
async def generate_incident_report(
    incident_id: UUID,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_viewer)],
    format: str = Query("json", pattern="^(json|md|pdf)$"),
) -> GenerateReportResponse:
    """Generate a structured incident report in JSON, Markdown, or PDF format."""
    builder = IncidentReportBuilder(session)
    doc = await builder.build_report(incident_id)

    if format == "json":
        data = ReportRenderers.render_json(doc)
        content_type = "application/json"
        ext = "json"
    elif format == "md":
        data = ReportRenderers.render_markdown(doc)
        content_type = "text/markdown"
        ext = "md"
    else:
        data = ReportRenderers.render_pdf(doc)
        content_type = "application/pdf"
        ext = "pdf"

    file_hash = hashlib.sha256(data).hexdigest()
    file_size = len(data)
    report_id = uuid.uuid4()
    now = datetime.now(timezone.utc)

    # Store in object store
    store = MinioObjectStore()
    object_name = f"{incident_id}/{report_id}_report.{ext}"
    storage_path = await store.put_object(
        bucket_name="reports",
        object_name=object_name,
        data=data,
        content_type=content_type,
    )

    orm = ReportOrm(
        id=report_id,
        incident_id=incident_id,
        format=format,
        storage_path=storage_path,
        file_hash_sha256=file_hash,
        file_size_bytes=file_size,
        generated_by=current_user.username,
        created_at=now,
    )
    session.add(orm)
    await session.flush()

    # Append REPORT_GENERATED to the cryptographic audit ledger
    ledger = HashChainLedger(session)
    await ledger.append_entry(
        entry_type=EntryType.REPORT_GENERATED,
        incident_id=incident_id,
        payload={
            "report_id": str(report_id),
            "format": format,
            "file_hash_sha256": file_hash,
            "file_size_bytes": file_size,
        },
    )

    return GenerateReportResponse(
        report_id=report_id,
        incident_id=incident_id,
        format=format,
        file_hash_sha256=file_hash,
        file_size_bytes=file_size,
        created_at=now,
        download_url=f"/api/v1/reports/{report_id}/download",
    )


@router.get("/{report_id}/download")
async def download_report(
    report_id: UUID,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[User, Depends(require_viewer)],
) -> Response:
    """Download a generated report artifact with media headers."""
    stmt = select(ReportOrm).where(ReportOrm.id == report_id)
    res = await session.execute(stmt)
    orm = res.scalar_one_or_none()
    if not orm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "REPORT_NOT_FOUND", "message": f"Report '{report_id}' not found"}},
        )

    parts = orm.storage_path.split("/", 1)
    bucket = parts[0]
    obj_name = parts[1] if len(parts) > 1 else orm.storage_path

    store = MinioObjectStore()
    data = await store.get_object(bucket, obj_name)

    content_types = {
        "json": "application/json",
        "md": "text/markdown",
        "pdf": "application/pdf",
    }
    media_type = content_types.get(orm.format, "application/octet-stream")

    return Response(
        content=data,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="report_{report_id}.{orm.format}"'},
    )
