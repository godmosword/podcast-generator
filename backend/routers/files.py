from __future__ import annotations

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from backend.jobs import get_job
from backend.utils.storage import get_storage

router = APIRouter(prefix="/api", tags=["files"])


@router.get("/files/{job_id}")
async def download_file(job_id: str) -> Response:
    job = get_job(job_id)
    if not job or not job.output_path:
        raise HTTPException(status_code=404, detail="File not found.")
    return get_storage().serve(str(job.output_path), job.output_path.name)
