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


# ==================== 新增 / 重構部分 ====================
jobs: dict[str, Job] = {}   # 記憶體快取（重啟後自動從 DB 補齊）


def get_job(job_id: str) -> "Job | None":
    """取得 Job，記憶體 miss 時自動從 DB 載入並快取"""
    if job_id in jobs:
        return jobs[job_id]

    job = load_job_from_db(job_id)
    if job:
        job.events = asyncio.Queue()          # 每次載入都重建 queue（無法持久化）
        jobs[job_id] = job
    return job


def create_job(
    job_id: str,
    status: JobStatus = "queued",
    progress: int = 0,
    message: str = "Queued",
    **kwargs: Any,
) -> Job:
    """統一建立新 Job 並立即持久化"""
    job = Job(
        id=job_id,
        status=status,
        progress=progress,
        message=message,
        **kwargs,
    )
    jobs[job_id] = job
    _persist(job)          # 初始狀態寫入 DB
    return job


def prune_jobs(
    ttl_seconds: int = DEFAULT_JOB_TTL_SECONDS,
    *,
    now: datetime | None = None,
    remove_files: bool = True,
) -> list[str]:
    """同時清理記憶體 + DB 中的過期任務"""
    current_time = now or datetime.now(timezone.utc)
    cutoff = current_time - timedelta(seconds=ttl_seconds)

    # 1. 清理記憶體
    stale_ids = [
        job_id
        for job_id, job in list(jobs.items())
        if job.updated_at < cutoff or (job.status in {"done", "failed"} and job.created_at < cutoff)
    ]

    for job_id in stale_ids:
        job = jobs.pop(job_id, None)
        if remove_files and job and job.output_path:
            try:
                job.output_path.unlink(missing_ok=True)
            except OSError:
                pass

    # 2. 清理 DB
    from backend.models.database import JobRecord, SessionLocal
    with SessionLocal() as session:
        session.query(JobRecord).filter(
            (JobRecord.updated_at < cutoff) |
            ((JobRecord.status.in_(["done", "failed"])) & (JobRecord.created_at < cutoff))
        ).delete()
        session.commit()

    return stale_ids
