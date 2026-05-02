from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
import os
from pathlib import Path
from typing import Any

from backend.models.schemas import JobStatus

DEFAULT_JOB_TTL_SECONDS = int(os.getenv("JOB_TTL_SECONDS", str(6 * 60 * 60)))


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
        event = {"id": self.id, "status": status, "progress": progress, "message": message, **extra}
        await self.events.put(event)


jobs: dict[str, Job] = {}


def prune_jobs(
    ttl_seconds: int = DEFAULT_JOB_TTL_SECONDS,
    *,
    now: datetime | None = None,
    remove_files: bool = True,
) -> list[str]:
    """Remove stale in-memory jobs and their generated output files."""
    current_time = now or datetime.now(timezone.utc)
    cutoff = current_time - timedelta(seconds=ttl_seconds)
    stale_ids = [
        job_id
        for job_id, job in jobs.items()
        if job.updated_at < cutoff or (job.status in {"done", "failed"} and job.created_at < cutoff)
    ]

    for job_id in stale_ids:
        job = jobs.pop(job_id)
        if remove_files and job.output_path:
            try:
                job.output_path.unlink(missing_ok=True)
            except OSError:
                pass

    return stale_ids
