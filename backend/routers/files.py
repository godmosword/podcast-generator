from __future__ import annotations

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from backend.jobs import jobs

router = APIRouter(prefix="/api", tags=["files"])


@router.get("/files/{job_id}")
async def download_file(job_id: str) -> FileResponse:
    job = jobs.get(job_id)
    if not job or not job.output_path or not job.output_path.exists():
        raise HTTPException(status_code=404, detail="File not found.")

    media_type = "audio/wav" if job.output_path.suffix == ".wav" else "audio/mpeg"
    return FileResponse(job.output_path, media_type=media_type, filename=job.output_path.name)
