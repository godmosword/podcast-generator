from __future__ import annotations

import json
import logging
import re
from typing import Any

logger = logging.getLogger(__name__)


def _ms_to_timestamp(ms: int) -> str:
    total_s = ms // 1000
    h = total_s // 3600
    m = (total_s % 3600) // 60
    s = total_s % 60
    if h:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


async def generate_show_notes(
    script: str,
    segments: list[dict[str, Any]],
    gemini_api_key: str,
    gemini_model: str = "gemini-2.0-flash",
) -> tuple[list[dict[str, Any]], str]:
    """Generate chapter markers and show notes using Gemini."""
    if not gemini_api_key:
        return [], ""

    timing_lines = "\n".join(
        f"{_ms_to_timestamp(s['start_ms'])} [{s['speaker']}] {s['text'][:80]}"
        for s in segments[:40]
    )

    prompt = (
        "You are a professional podcast show notes writer. "
        "Based on the script and timing below, generate:\n"
        "1. Chapter markers (key topic shifts)\n"
        "2. Show notes in Markdown (summary + key topics)\n\n"
        f"Script (first 6000 chars):\n{script[:6000]}\n\n"
        f"Timing (first 40 segments):\n{timing_lines}\n\n"
        "Respond ONLY with valid JSON in this exact format:\n"
        '{"chapters": [{"time_ms": 0, "timestamp": "00:00", "title": "Introduction"}, ...], '
        '"show_notes": "## Summary\\n..."}'
    )

    try:
        from google import genai

        client = genai.Client(api_key=gemini_api_key)
        response = await client.aio.models.generate_content(
            model=gemini_model,
            contents=prompt,
        )
        raw = response.text or ""
        json_match = re.search(r"\{.*\}", raw, re.DOTALL)
        if not json_match:
            return [], ""
        data = json.loads(json_match.group())
        chapters: list[dict[str, Any]] = data.get("chapters") or []
        show_notes: str = str(data.get("show_notes") or "")
        return chapters, show_notes
    except Exception as exc:
        logger.warning("generate_show_notes failed: %s", exc)
        return [], ""
