from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request
from fastapi.responses import StreamingResponse

from backend.jobs import Job, jobs, load_job_from_db, prune_jobs
from backend.models.schemas import GenerateRequest, GenerateResponse, JobSnapshot
from backend.bgm_catalog import BgmNotFoundError, get_bgm_track
from backend.config import voice_provider
from backend.security import enforce_rate_limit
from config import Config, Provider
from core.script_parser import parse_script_details
from pipeline.podcast_pipeline import PodcastPipeline

router = APIRouter(prefix="/api", tags=["generate"])
logger = logging.getLogger(__name__)
GENERIC_GENERATE_ERROR = "Audio synthesis failed. Please try again."


@router.post("/generate", response_model=GenerateResponse)
async def generate(request: Request, payload: GenerateRequest, background_tasks: BackgroundTasks) -> GenerateResponse:
    runtime_config = Config()
    enforce_rate_limit(
        request,
        runtime_config,
        bucket="generate",
        limit_per_minute=runtime_config.rate_limit_generate_per_minute,
    )
    prune_jobs()
    parsed = parse_script_details(payload.script)
    if parsed.speaker_count > payload.host_count:
        raise HTTPException(status_code=400, detail=f"Script has {parsed.speaker_count} speakers but host_count is {payload.host_count}.")
    if parsed.speaker_count > 4:
        raise HTTPException(status_code=400, detail="Only 1-4 speakers are supported.")
    providers = {voice_provider(item.voice) for item in payload.voice_assignments}
    if len(providers) > 1:
        raise HTTPException(status_code=400, detail="Mixed TTS providers are not supported in one job yet.")
    if payload.audio.bgm_enabled and payload.audio.bgm_id:
        try:
            get_bgm_track(payload.audio.bgm_id)
        except BgmNotFoundError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    job_id = uuid4().hex
    job = Job(id=job_id)
    jobs[job_id] = job
    await job.publish("queued", 0, "Queued.")
    background_tasks.add_task(_run_job, job_id, payload)
    return GenerateResponse(job_id=job_id, events_url=f"/api/generate/{job_id}/events", file_url=None)


@router.get("/generate/{job_id}", response_model=JobSnapshot)
async def get_job(job_id: str) -> JobSnapshot:
    job = _job_or_404(job_id)
    return _snapshot(job)


@router.get("/generate/{job_id}/events")
async def stream_events(job_id: str) -> StreamingResponse:
    job = _job_or_404(job_id)

    async def event_stream():
        snapshot = _snapshot(job).model_dump()
        yield _format_sse(snapshot)
        if snapshot["status"] in {"done", "failed"}:
            return
        while True:
            event = await job.events.get()
            yield _format_sse(event)
            if event["status"] in {"done", "failed"}:
                break

    return StreamingResponse(event_stream(), media_type="text/event-stream")


async def _run_job(job_id: str, request: GenerateRequest) -> None:
    job = jobs[job_id]
    output_format = request.audio.output_format
    output_path = Path("output") / f"{job_id}.{output_format}"
    config = Config()
    selected_providers = {voice_provider(item.voice) for item in request.voice_assignments}
    if selected_providers:
        config.provider = selected_providers.pop()
    config.segment_pause_ms = request.audio.pause_ms
    config.speech_speed = request.audio.speed
    config.voice_mode = request.audio.voice_mode
    config.voice_quality = request.audio.voice_quality
    if config.voice_quality == "high" and config.provider == Provider.OPENAI:
        config.openai_model = "tts-1-hd"
    if request.audio.bgm_enabled and request.audio.bgm_id:
        config.bgm_path = str(get_bgm_track(request.audio.bgm_id).path)
    config.bgm_volume_db = request.audio.bgm_volume_db
    pipeline = PodcastPipeline(config)
    metadata = {"year": datetime.now().year}
    if request.title:
        metadata["title"] = request.title
    if request.artist:
        metadata["artist"] = request.artist
    if request.album:
        metadata["album"] = request.album

    overrides = {
        item.role: item.voice
        for item in request.voice_assignments
        if voice_provider(item.voice) == config.provider
    }

    async def publish(status: str, progress: int, message: str) -> None:
        await job.publish(status, progress, message)

    try:
        result = await pipeline.run_text(
            request.script,
            str(output_path),
            metadata=metadata,
            voice_overrides=overrides,
            output_format=output_format,
            normalize=request.audio.normalize,
            bgm_enabled=request.audio.bgm_enabled,
            bgm_path=config.bgm_path,
            bgm_volume_db=request.audio.bgm_volume_db,
            bgm_fade_ms=request.audio.bgm_fade_ms,
            progress=publish,
        )
        job.output_path = Path(result)
        await job.publish("done", 100, "Done.", file_url=f"/api/files/{job_id}")
    except Exception as exc:
        logger.exception("Generate job failed", extra={"job_id": job_id})
        job.error = GENERIC_GENERATE_ERROR
        await job.publish("failed", job.progress, GENERIC_GENERATE_ERROR, error=GENERIC_GENERATE_ERROR)


def _job_or_404(job_id: str) -> Job:
    job = jobs.get(job_id) or load_job_from_db(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")
    return job


def _snapshot(job: Job) -> JobSnapshot:
    return JobSnapshot(
        id=job.id,
        status=job.status,
        progress=job.progress,
        message=job.message,
        file_url=f"/api/files/{job.id}" if job.output_path else None,
        error=job.error,
    )


def _format_sse(payload: dict) -> str:
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"
