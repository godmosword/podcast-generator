from __future__ import annotations

import io
import logging

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydub import AudioSegment

from backend.config import voice_provider
from backend.models.schemas import PreviewRequest
from backend.security import enforce_rate_limit
from config import Config
from pipeline.podcast_pipeline import _build_provider

router = APIRouter(prefix="/api", tags=["preview"])
logger = logging.getLogger(__name__)
GENERIC_PREVIEW_ERROR = "Voice preview failed. Please try again."


@router.post("/preview")
async def preview(request: Request, payload: PreviewRequest) -> StreamingResponse:
    config = Config(provider=voice_provider(payload.voice))
    enforce_rate_limit(
        request,
        config,
        bucket="preview",
        limit_per_minute=config.rate_limit_preview_per_minute,
    )
    try:
        provider = _build_provider(config)
        raw = await provider.synthesize(payload.text, payload.voice, **config.tts_options_for(payload.voice))
        audio = AudioSegment.from_file(io.BytesIO(raw), format="mp3")[: payload.seconds * 1000]
    except Exception as exc:
        logger.exception("Voice preview failed")
        raise HTTPException(status_code=503, detail=GENERIC_PREVIEW_ERROR) from exc

    buffer = io.BytesIO()
    audio.export(buffer, format="mp3", bitrate="128k")
    buffer.seek(0)
    return StreamingResponse(buffer, media_type="audio/mpeg")
