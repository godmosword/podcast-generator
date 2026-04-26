from __future__ import annotations

import io

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydub import AudioSegment

from backend.config import voice_provider
from backend.models.schemas import PreviewRequest
from config import Config
from pipeline.podcast_pipeline import _build_provider

router = APIRouter(prefix="/api", tags=["preview"])


@router.post("/preview")
async def preview(request: PreviewRequest) -> StreamingResponse:
    config = Config(provider=voice_provider(request.voice))
    provider = _build_provider(config)
    raw = await provider.synthesize(request.text, request.voice)
    audio = AudioSegment.from_file(io.BytesIO(raw), format="mp3")[: request.seconds * 1000]
    buffer = io.BytesIO()
    audio.export(buffer, format="mp3", bitrate="128k")
    buffer.seek(0)
    return StreamingResponse(buffer, media_type="audio/mpeg")
