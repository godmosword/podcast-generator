from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
import os
from pathlib import Path
from typing import Any

from backend.models.schemas import JobStatus

DEFAULT_JOB_TTL_SECONDS = int(os.getenv("JOB_TTL_SECONDS", str(6 * 60 * 60)))


def _persist(job: "Job") -> None:
    from backend.models.database import JobRecord, SessionLocal

    with SessionLocal() as session:
        record = session.get(JobRecord, job.id)
        if record is None:
            record = JobRecord(id=job.id, created_at=job.created_at)
            session.add(record)
        record.status = job.status
        record.progress = job.progress
        record.message = job.message
        record.output_path = str(job.output_path) if job.output_path else None
        record.error = job.error
        record.retry_count = job.retry_count
        record.last_provider = job.last_provider
        record.request_payload = job.request_payload
        record.updated_at = job.updated_at
        session.commit()


def load_job_from_db(job_id: str) -> "Job | None":
    from backend.models.database import JobRecord, SessionLocal

    with SessionLocal() as session:
        record = session.get(JobRecord, job_id)
        if record is None:
            return None
        return Job(
            id=record.id,
            status=record.status,
            progress=record.progress,
            message=record.message or "",
            output_path=Path(record.output_path) if record.output_path else None,
            error=record.error,
            retry_count=record.retry_count or 0,
            last_provider=record.last_provider,
            request_payload=record.request_payload,
            created_at=record.created_at.replace(tzinfo=timezone.utc),
            updated_at=record.updated_at.replace(tzinfo=timezone.utc),
        )


@dataclass
class Job:
    id: str
    status: JobStatus = "queued"
    progress: int = 0
    message: str = "Queued"
    output_path: Path | None = None
    error: str | None = None
    retry_count: int = 0
    last_provider: str | None = None
    request_payload: str | None = None  # JSON-serialised GenerateRequest
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    events: asyncio.Queue[dict[str, Any]] = field(default_factory=asyncio.Queue)

    async def publish(self, status: JobStatus, progress: int, message: str, **extra: Any) -> None:
        self.status = status
        self.progress = progress
        self.message = message
        self.updated_at = datetime.now(timezone.utc)
        _persist(self)
        event = {"id": self.id, "status": status, "progress": progress, "message": message, **extra}
        await self.events.put(event)


jobs: dict[str, Job] = {}


def get_job(job_id: str) -> "Job | None":
    """Return Job, loading from DB on cache miss."""
    if job_id in jobs:
        return jobs[job_id]
    job = load_job_from_db(job_id)
    if job:
        job.events = asyncio.Queue()
        jobs[job_id] = job
    return job


def create_job(
    job_id: str,
    status: JobStatus = "queued",
    progress: int = 0,
    message: str = "Queued",
    **kwargs: Any,
) -> Job:
    """Create a new Job and immediately persist it."""
    job = Job(id=job_id, status=status, progress=progress, message=message, **kwargs)
    jobs[job_id] = job
    _persist(job)
    return job


def prune_jobs(
    ttl_seconds: int = DEFAULT_JOB_TTL_SECONDS,
    *,
    now: datetime | None = None,
    remove_files: bool = True,
) -> list[str]:
    """Evict stale jobs from memory and delete them from the DB."""
    current_time = now or datetime.now(timezone.utc)
    cutoff = current_time - timedelta(seconds=ttl_seconds)

    stale_ids = [
        job_id
        for job_id, job in list(jobs.items())
        if job.updated_at < cutoff or (job.status in {"done", "failed"} and job.created_at < cutoff)
    ]

    for job_id in stale_ids:
        job = jobs.pop(job_id, None)
        if remove_files and job and job.output_path:
            from backend.utils.storage import get_storage
            get_storage().delete(str(job.output_path))

    from backend.models.database import JobRecord, SessionLocal
    with SessionLocal() as session:
        session.query(JobRecord).filter(
            (JobRecord.updated_at < cutoff)
            | (
                JobRecord.status.in_(["done", "failed"])
                & (JobRecord.created_at < cutoff)
            )
        ).delete()
        session.commit()

    return stale_ids
