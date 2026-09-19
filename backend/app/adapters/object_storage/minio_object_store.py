"""Object storage adapter for MinIO S3-compatible evidence and report persistence."""

from __future__ import annotations

import io
from pathlib import Path
from typing import Any

from minio import Minio

from app.config.settings import get_settings


class MinioObjectStore:
    """MinIO S3 storage client with local filesystem fallback."""

    def __init__(self) -> None:
        self._settings = get_settings()
        self._client: Minio | None = None
        self._local_storage_path = Path(__file__).resolve().parent.parent.parent.parent / "storage"
        self._local_storage_path.mkdir(parents=True, exist_ok=True)

    def _get_client(self) -> Minio | None:
        """Lazily initialize MinIO client if accessible."""
        if self._client is None:
            try:
                self._client = Minio(
                    self._settings.minio_endpoint,
                    access_key=self._settings.minio_access_key,
                    secret_key=self._settings.minio_secret_key,
                    secure=self._settings.minio_use_ssl,
                )
            except Exception:
                self._client = None
        return self._client

    async def put_object(
        self,
        bucket_name: str,
        object_name: str,
        data: bytes,
        content_type: str = "application/octet-stream",
    ) -> str:
        """Store bytes into MinIO bucket or fallback directory."""
        client = self._get_client()
        if client:
            try:
                if not client.bucket_exists(bucket_name):
                    client.make_bucket(bucket_name)
                client.put_object(
                    bucket_name=bucket_name,
                    object_name=object_name,
                    data=io.BytesIO(data),
                    length=len(data),
                    content_type=content_type,
                )
                return f"{bucket_name}/{object_name}"
            except Exception:
                pass

        # Local filesystem fallback
        bucket_dir = self._local_storage_path / bucket_name
        bucket_dir.mkdir(parents=True, exist_ok=True)
        target_file = bucket_dir / object_name
        target_file.parent.mkdir(parents=True, exist_ok=True)
        with open(target_file, "wb") as f:
            f.write(data)
        return f"{bucket_name}/{object_name}"

    async def get_object(self, bucket_name: str, object_name: str) -> bytes:
        """Retrieve stored bytes from MinIO or fallback directory."""
        client = self._get_client()
        if client:
            try:
                response = client.get_object(bucket_name, object_name)
                data: bytes = response.read()
                response.close()
                response.release_conn()
                return data
            except Exception:
                pass

        # Fallback
        target_file = self._local_storage_path / bucket_name / object_name
        if not target_file.exists():
            raise FileNotFoundError(f"Object '{bucket_name}/{object_name}' not found.")
        with open(target_file, "rb") as f:
            return f.read()
