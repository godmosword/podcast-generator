from __future__ import annotations

import time
from collections import defaultdict
from typing import Literal

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from config import Config
from core.script_generator import ScriptSpec, generate_script

router = APIRouter(prefix="/api", tags=["script"])

# Simple in-memory rate limiter: max 10 requests per 60 seconds per IP
_rate_buckets: dict[str, list[float]] = defaultdict(list)
_RATE_WINDOW_SEC = 60
_RATE_MAX = 10


class ScriptGenerationRequest(BaseModel):
    topic: str = Field(min_length=1, max_length=200)
    duration_min: int = Field(default=10, ge=5, le=20)
    host_count: int = Field(default=2, ge=1, le=4)
    tone: Literal["educational", "entertainment", "storytelling", "interview", "debate"] = "educational"
    language: Literal["zh-TW", "zh-CN", "en", "ja"] = "zh-TW"
    extra_context: str | None = Field(default=None, max_length=500)


class ScriptGenerationResponse(BaseModel):
    script: str
    estimated_duration_sec: int
    warnings: list[str]


@router.post("/script/generate", response_model=ScriptGenerationResponse)
async def generate_script_endpoint(
    body: ScriptGenerationRequest,
    request: Request,
) -> ScriptGenerationResponse:
    config = Config()
    if not config.anthropic_api_key:
        raise HTTPException(status_code=503, detail="ANTHROPIC_API_KEY is not configured on the server.")

    client_ip = request.client.host if request.client else "unknown"
    now = time.monotonic()
    bucket = _rate_buckets[client_ip]
    _rate_buckets[client_ip] = [t for t in bucket if now - t < _RATE_WINDOW_SEC]
    if len(_rate_buckets[client_ip]) >= _RATE_MAX:
        raise HTTPException(status_code=429, detail="Rate limit exceeded. Please wait before generating another script.")
    _rate_buckets[client_ip].append(now)

    spec = ScriptSpec(
        topic=body.topic,
        duration_min=body.duration_min,
        host_count=body.host_count,
        tone=body.tone,
        language=body.language,
        extra_context=body.extra_context,
    )

    try:
        draft = await generate_script(spec, config.anthropic_api_key)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Script generation failed: {exc}") from exc

    return ScriptGenerationResponse(
        script=draft.script,
        estimated_duration_sec=draft.estimated_duration_sec,
        warnings=draft.warnings,
    )
