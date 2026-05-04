from __future__ import annotations

import os
from abc import ABC, abstractmethod
from pathlib import Path

from fastapi import HTTPException
from fastapi.responses import FileResponse, RedirectResponse, Response


class OutputStorage(ABC):
    @abstractmethod
    def save(self, local_path: Path, job_id: str) -> str:
        """Persist file and return storage key to store in job.output_path."""

    @abstractmethod
    def delete(self, key: str) -> None:
        """Delete file by storage key."""

    @abstractmethod
    def serve(self, key: str, filename: str) -> Response:
        """Return FastAPI response for downloading the file."""


class LocalStorage(OutputStorage):
    def save(self, local_path: Path, job_id: str) -> str:
        return str(local_path)

    def delete(self, key: str) -> None:
        try:
            Path(key).unlink(missing_ok=True)
        except OSError:
            pass

    def serve(self, key: str, filename: str) -> Response:
        path = Path(key)
        if not path.exists():
            raise HTTPException(status_code=404, detail="File not found.")
        media_type = "audio/wav" if path.suffix == ".wav" else "audio/mpeg"
        return FileResponse(path, media_type=media_type, filename=filename)


class S3Storage(OutputStorage):
    _S3_PREFIX = "s3:"

    def __init__(self) -> None:
        import boto3

        self._bucket = os.environ["S3_BUCKET"]
        region = os.getenv("S3_REGION", "us-east-1")
        self._client = boto3.client("s3", region_name=region)

    def save(self, local_path: Path, job_id: str) -> str:
        key = f"output/{local_path.name}"
        self._client.upload_file(str(local_path), self._bucket, key)
        try:
            local_path.unlink(missing_ok=True)
        except OSError:
            pass
        return f"{self._S3_PREFIX}{key}"

    def delete(self, key: str) -> None:
        s3_key = key.removeprefix(self._S3_PREFIX)
        try:
            self._client.delete_object(Bucket=self._bucket, Key=s3_key)
        except Exception:
            pass

    def serve(self, key: str, filename: str) -> Response:
        s3_key = key.removeprefix(self._S3_PREFIX)
        url = self._client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self._bucket, "Key": s3_key},
            ExpiresIn=3600,
        )
        return RedirectResponse(url=url, status_code=302)


_storage: OutputStorage | None = None


def get_storage() -> OutputStorage:
    global _storage
    if _storage is None:
        backend = os.getenv("STORAGE_BACKEND", "local").lower()
        _storage = S3Storage() if backend == "s3" else LocalStorage()
    return _storage
