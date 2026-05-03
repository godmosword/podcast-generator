from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request
from fastapi.responses import StreamingResponse

from backend.jobs import Job, create_job, get_job, prune_jobs
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

# Provider fallback order (most capable → most reliable).
# Edge is always available; paid providers require API keys.
_FALLBACK_CHAIN = [Provider.ELEVENLABS, Provider.OPENAI, Provider.EDGE]


def _available_providers(config: Config) -> list[Provider]:
    """Return providers that have credentials, in fallback order."""
    out: list[Provider] = []
    for p in _FALLBACK_CHAIN:
        if p == Provider.EDGE:
            out.append(p)
        elif p == Provider.OPENAI and config.openai_api_key:
            out.append(p)
        elif p == Provider.ELEVENLABS and config.elevenlabs_api_key:
            out.append(p)
    return out


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
    job = create_job(job_id, request_payload=payload.model_dump_json())
    await job.publish("queued", 0, "Queued.")
    background_tasks.add_task(_run_job, job_id, payload)
    return GenerateResponse(job_id=job_id, events_url=f"/api/generate/{job_id}/events", file_url=None)


@router.post("/generate/{job_id}/retry", response_model=GenerateResponse)
async def retry_job(job_id: str, background_tasks: BackgroundTasks) -> GenerateResponse:
    job = _job_or_404(job_id)
    if job.status not in {"failed", "done"}:
        raise HTTPException(status_code=409, detail="Only failed or completed jobs can be retried.")
    if not job.request_payload:
        raise HTTPException(status_code=422, detail="Original request payload not found; cannot retry.")

    payload = GenerateRequest.model_validate_json(job.request_payload)

    # Reset job state for re-run.
    job.status = "queued"
    job.progress = 0
    job.error = None
    job.output_path = None
    job.retry_count += 1
    job.last_provider = None
    job.message = f"Retry #{job.retry_count} queued."
    await job.publish("queued", 0, job.message)

    background_tasks.add_task(_run_job, job_id, payload)
    return GenerateResponse(job_id=job_id, events_url=f"/api/generate/{job_id}/events", file_url=None)


@router.get("/generate/{job_id}", response_model=JobSnapshot)
async def get_job_status(job_id: str) -> JobSnapshot:
    return _snapshot(_job_or_404(job_id))


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
    job = get_job(job_id)
    if job is None:
        logger.error("_run_job called for unknown job %s", job_id)
        return

    output_format = request.audio.output_format
    output_path = Path("output") / f"{job_id}.{output_format}"

    base_config = Config()
    base_config.segment_pause_ms = request.audio.pause_ms
    base_config.speech_speed = request.audio.speed
    base_config.voice_mode = request.audio.voice_mode
    base_config.voice_quality = request.audio.voice_quality
    if request.audio.bgm_enabled and request.audio.bgm_id:
        base_config.bgm_path = str(get_bgm_track(request.audio.bgm_id).path)
    base_config.bgm_volume_db = request.audio.bgm_volume_db

    metadata = {"year": datetime.now().year}
    if request.title:
        metadata["title"] = request.title
    if request.artist:
        metadata["artist"] = request.artist
    if request.album:
        metadata["album"] = request.album

    # Determine requested provider from voice assignments.
    selected = {voice_provider(item.voice) for item in request.voice_assignments}
    primary = selected.pop() if selected else base_config.provider

    # Build fallback chain: requested provider first, then others with valid keys.
    available = _available_providers(base_config)
    fallback_chain = [primary] + [p for p in available if p != primary]

    last_error = GENERIC_GENERATE_ERROR
    for attempt_idx, provider in enumerate(fallback_chain):
        config = Config()
        config.segment_pause_ms = base_config.segment_pause_ms
        config.speech_speed = base_config.speech_speed
        config.voice_mode = base_config.voice_mode
        config.voice_quality = base_config.voice_quality
        config.bgm_path = base_config.bgm_path
        config.bgm_volume_db = base_config.bgm_volume_db
        config.provider = provider
        if config.voice_quality == "high" and provider == Provider.OPENAI:
            config.openai_model = "tts-1-hd"

        job.last_provider = provider.value

        if attempt_idx > 0:
            job.retry_count += 1
            msg = f"Provider {fallback_chain[attempt_idx - 1].value} failed. Trying {provider.value}…"
            logger.warning(msg)
            await job.publish("synthesizing", job.progress, msg)

        # Voice overrides are provider-specific; only apply them for the matching provider.
        overrides = {
            item.role: item.voice
            for item in request.voice_assignments
            if voice_provider(item.voice) == provider
        }

        pipeline = PodcastPipeline(config)

        async def publish(status: str, progress: int, message: str) -> None:
            await job.publish(status, progress, message)  # type: ignore[arg-type]

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
            return  # success — stop trying more providers
        except Exception as exc:
            last_error = str(exc)
            logger.warning("Provider %s failed for job %s: %s", provider.value, job_id, exc)

    # All providers exhausted.
    logger.exception("Generate job %s failed after all providers.", job_id)
    providers_tried = ", ".join(p.value for p in fallback_chain)
    error_msg = f"TTS synthesis failed after trying: {providers_tried}. {GENERIC_GENERATE_ERROR}"
    job.error = error_msg
    await job.publish("failed", job.progress, error_msg, error=error_msg)


def _job_or_404(job_id: str) -> Job:
    job = get_job(job_id)
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
        retry_count=job.retry_count,
        last_provider=job.last_provider,
    )


def _format_sse(payload: dict) -> str:
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"
