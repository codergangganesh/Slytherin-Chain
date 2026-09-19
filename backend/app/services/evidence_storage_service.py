"""Evidence storage service managing files and SHA-256 integrity verification."""

from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.object_storage.minio_object_store import MinioObjectStore
from app.db.orm_models import EvidenceItemOrm
from app.domain.enums import EntryType
from app.services.integrity.hash_chain_ledger import HashChainLedger


@dataclass(frozen=True)
class EvidenceItem:
    """Represents an authenticated evidence artifact."""

    id: UUID
    incident_id: UUID
    filename: str
    content_type: str
    file_size_bytes: int
    file_hash_sha256: str
    storage_path: str
    collected_by: str
    description: str
    created_at: datetime


class EvidenceStorageService:
    """Stores evidence artifacts in object storage and cryptographically anchors their hashes."""

    def __init__(
        self,
        session: AsyncSession,
        object_store: MinioObjectStore | None = None,
    ) -> None:
        self._session = session
        self._store = object_store or MinioObjectStore()
        self._ledger = HashChainLedger(session)

    async def store_evidence(
        self,
        incident_id: UUID,
        filename: str,
        data: bytes,
        content_type: str = "application/json",
        collected_by: str = "system",
        description: str = "",
    ) -> EvidenceItem:
        """Store evidence bytes, calculate SHA-256 hash, and record in audit ledger."""
        file_hash = hashlib.sha256(data).hexdigest()
        file_size = len(data)
        item_id = uuid.uuid4()
        now = datetime.now(UTC)

        object_name = f"{incident_id}/{item_id}_{filename}"
        storage_path = await self._store.put_object(
            bucket_name="evidence",
            object_name=object_name,
            data=data,
            content_type=content_type,
        )

        orm = EvidenceItemOrm(
            id=item_id,
            incident_id=incident_id,
            filename=filename,
            content_type=content_type,
            file_size_bytes=file_size,
            file_hash_sha256=file_hash,
            storage_path=storage_path,
            collected_by=collected_by,
            description=description,
            created_at=now,
        )
        self._session.add(orm)
        await self._session.flush()

        # Append EVIDENCE_ADDED to audit ledger
        await self._ledger.append_entry(
            entry_type=EntryType.EVIDENCE_ADDED,
            incident_id=incident_id,
            payload={
                "evidence_id": str(item_id),
                "filename": filename,
                "file_hash_sha256": file_hash,
                "file_size_bytes": file_size,
            },
        )

        return EvidenceItem(
            id=item_id,
            incident_id=incident_id,
            filename=filename,
            content_type=content_type,
            file_size_bytes=file_size,
            file_hash_sha256=file_hash,
            storage_path=storage_path,
            collected_by=collected_by,
            description=description,
            created_at=now,
        )

    async def get_evidence_data_and_verify(
        self, evidence_id: UUID
    ) -> tuple[bytes, bool, EvidenceItem | None]:
        """Retrieve evidence bytes and verify against stored SHA-256 hash."""
        stmt = select(EvidenceItemOrm).where(EvidenceItemOrm.id == evidence_id)
        res = await self._session.execute(stmt)
        orm = res.scalar_one_or_none()
        if not orm:
            return b"", False, None

        parts = orm.storage_path.split("/", 1)
        bucket = parts[0]
        obj_name = parts[1] if len(parts) > 1 else orm.storage_path

        data = await self._store.get_object(bucket, obj_name)
        recomputed_hash = hashlib.sha256(data).hexdigest()
        is_valid = recomputed_hash.lower() == orm.file_hash_sha256.lower()

        item = EvidenceItem(
            id=orm.id,
            incident_id=orm.incident_id,
            filename=orm.filename,
            content_type=orm.content_type,
            file_size_bytes=orm.file_size_bytes,
            file_hash_sha256=orm.file_hash_sha256,
            storage_path=orm.storage_path,
            collected_by=orm.collected_by,
            description=orm.description,
            created_at=orm.created_at,
        )
        return data, is_valid, item
