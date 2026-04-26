from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from backend.models.schemas import JobStatus


@dataclass
class Job:
    id: str
    status: JobStatus = "queued"
    progress: int = 0
    message: str = "Queued"
    output_path: Path | None = None
    error: str | None = None
    events: asyncio.Queue[dict[str, Any]] = field(default_factory=asyncio.Queue)

    async def publish(self, status: JobStatus, progress: int, message: str, **extra: Any) -> None:
        self.status = status
        self.progress = progress
        self.message = message
        event = {"id": self.id, "status": status, "progress": progress, "message": message, **extra}
        await self.events.put(event)


jobs: dict[str, Job] = {}
