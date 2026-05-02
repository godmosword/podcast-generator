from __future__ import annotations

import logging
from typing import Literal

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from backend.security import enforce_rate_limit
from config import Config
from core.script_generator import ScriptSpec, generate_script

router = APIRouter(prefix="/api", tags=["script"])
logger = logging.getLogger(__name__)


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
    enforce_rate_limit(request, config, bucket="script", limit_per_minute=config.rate_limit_ai_per_minute)
    if not config.gemini_api_key:
        raise HTTPException(status_code=503, detail="GEMINI_API_KEY is not configured on the server.")

    spec = ScriptSpec(
        topic=body.topic,
        duration_min=body.duration_min,
        host_count=body.host_count,
        tone=body.tone,
        language=body.language,
        extra_context=body.extra_context,
    )

    try:
        draft = await generate_script(spec, config.gemini_api_key, config.gemini_model)
    except Exception as exc:
        logger.exception("Script generation failed")
        raise HTTPException(status_code=500, detail="Script generation failed. Please try again.") from exc

    return ScriptGenerationResponse(
        script=draft.script,
        estimated_duration_sec=draft.estimated_duration_sec,
        warnings=draft.warnings,
    )
