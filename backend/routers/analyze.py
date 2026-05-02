from __future__ import annotations

import json
import logging
import re
from typing import Literal

import anthropic
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from backend.security import enforce_rate_limit
from config import Config

router = APIRouter(prefix="/api", tags=["analyze"])
logger = logging.getLogger(__name__)

_LANG_LABELS = {
    "zh-TW": "繁體中文",
    "zh-CN": "简体中文",
    "en": "English",
    "ja": "日本語",
}

_SYSTEM_PROMPT = """\
You are an expert podcast content analyst. Analyze the given text for:

1. LOGICAL FLOW — clear idea progression, smooth transitions, coherent buildup from intro to conclusion
2. GAPS — missing information, unexplained jumps in reasoning, topics mentioned but not adequately addressed
3. BOUNDARY CONDITIONS — edge cases, exceptions, unstated assumptions, counterarguments not addressed
4. STRENGTHS — compelling or well-structured aspects particularly suitable for podcast discussion
5. SUGGESTIONS — concrete improvements before generating a podcast script (e.g., "Add a concrete example for claim X", "Clarify the relationship between Y and Z")

Return ONLY a valid JSON object matching this exact schema — no markdown fences, no extra text:
{
  "logical_score": <integer 0-100>,
  "summary": "<1-2 sentence overall assessment>",
  "findings": [
    {
      "type": "<gap|boundary|suggestion|strength>",
      "severity": "<info|warning|critical>",
      "content": "<specific, actionable finding referencing actual content>"
    }
  ],
  "enriched_context": "<200-300 word synthesis of key insights, gaps addressed, and special considerations for the script writer>"
}

Be specific and actionable. Reference actual content from the text, not generic observations.\
"""


class AnalyzeRequest(BaseModel):
    text: str = Field(min_length=10, max_length=8000)
    topic: str | None = Field(default=None, max_length=200)
    language: Literal["zh-TW", "zh-CN", "en", "ja"] = "zh-TW"


class AnalysisFinding(BaseModel):
    type: Literal["gap", "boundary", "suggestion", "strength"]
    severity: Literal["info", "warning", "critical"]
    content: str


class AnalyzeResponse(BaseModel):
    logical_score: int
    summary: str
    findings: list[AnalysisFinding]
    enriched_context: str


def _fallback_response(reason: str) -> AnalyzeResponse:
    return AnalyzeResponse(
        logical_score=50,
        summary=f"分析無法完成：{reason}",
        findings=[],
        enriched_context="",
    )


def _strip_fence(raw: str) -> str:
    raw = raw.strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\n?", "", raw).rstrip("`").strip()
    return raw


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_text(body: AnalyzeRequest, request: Request) -> AnalyzeResponse:
    config = Config()
    enforce_rate_limit(request, config, bucket="analyze", limit_per_minute=config.rate_limit_ai_per_minute)
    if not config.anthropic_api_key:
        raise HTTPException(status_code=503, detail="ANTHROPIC_API_KEY is not configured on the server.")

    lang_label = _LANG_LABELS.get(body.language, "繁體中文")
    user_parts = []
    if body.topic:
        user_parts.append(f"Topic: {body.topic}")
    user_parts.append(f"Text to analyze:\n\n{body.text}")
    if body.language != "en":
        user_parts.append(
            f"\nPlease write all 'content' values, 'summary', and 'enriched_context' in {lang_label}."
        )
    user_content = "\n\n".join(user_parts)

    client = anthropic.AsyncAnthropic(api_key=config.anthropic_api_key)
    try:
        message = await client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=2048,
            system=_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_content}],
        )
    except Exception as exc:
        logger.exception("Analysis failed")
        raise HTTPException(status_code=500, detail="Analysis failed. Please try again.") from exc

    raw = _strip_fence(message.content[0].text)
    try:
        data = json.loads(raw)
        findings = [AnalysisFinding(**f) for f in data.get("findings", [])]
        return AnalyzeResponse(
            logical_score=int(data.get("logical_score", 50)),
            summary=data.get("summary", ""),
            findings=findings,
            enriched_context=data.get("enriched_context", ""),
        )
    except (json.JSONDecodeError, KeyError, TypeError, ValueError):
        return _fallback_response("JSON 解析錯誤")
