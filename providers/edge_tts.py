from __future__ import annotations

import io
import re

import edge_tts
from pydub import AudioSegment

from backend.voice_catalog import provider_voice_id
from providers.base import AbstractTTSProvider

# Pause durations injected between synthesized clauses (ms)
_CLAUSE_PAUSE_MS: dict[str, int] = {
    "，": 180, ",": 150,
    "。": 380, ".": 280,
    "！": 320, "!": 280,
    "？": 320, "?": 280,
    "；": 220, ";": 180,
    "\n": 200,
}

_CLAUSE_SPLIT_RE = re.compile(r"(?<=[。！？，,；;!?\n])\s*")


class EdgeTTSProvider(AbstractTTSProvider):
    """Microsoft Edge TTS with sentence-level segmentation for natural pauses."""

    async def synthesize(self, text: str, voice: str, **kwargs) -> bytes:
        speed = float(kwargs.get("speed", 1.0))
        rate = kwargs.get("rate") or _speed_to_rate(speed)
        pitch = str(kwargs.get("pitch", "+0Hz"))
        pause_scale = float(kwargs.get("pause_scale", 1.0))

        voice_id = str(kwargs.get("provider_voice_id") or provider_voice_id(voice))
        clauses = _split_clauses(text)

        if len(clauses) <= 1:
            return await _synthesize_one(clauses[0] if clauses else text, voice_id, rate, pitch)

        combined = AudioSegment.empty()
        for i, clause in enumerate(clauses):
            raw = await _synthesize_one(clause, voice_id, rate, pitch)
            if raw:
                combined += AudioSegment.from_file(io.BytesIO(raw), format="mp3")
            if i < len(clauses) - 1:
                pause_ms = int(_trailing_pause_ms(clause) * pause_scale)
                if pause_ms > 0:
                    combined += AudioSegment.silent(duration=pause_ms)

        out = io.BytesIO()
        combined.export(out, format="mp3", bitrate="128k")
        out.seek(0)
        return out.read()


async def _synthesize_one(text: str, voice_id: str, rate: str, pitch: str) -> bytes:
    if not text.strip():
        return b""
    communicate = edge_tts.Communicate(text, voice_id, rate=rate, pitch=pitch)
    buffer = io.BytesIO()
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            buffer.write(chunk["data"])
    buffer.seek(0)
    return buffer.read()


def _split_clauses(text: str) -> list[str]:
    clauses = _CLAUSE_SPLIT_RE.split(text.strip())
    return [c for c in clauses if c.strip()]


def _trailing_pause_ms(clause: str) -> int:
    stripped = clause.rstrip()
    if not stripped:
        return 0
    return _CLAUSE_PAUSE_MS.get(stripped[-1], 0)


def _speed_to_rate(speed: float) -> str:
    percent = round((speed - 1.0) * 100)
    percent = max(-50, min(50, percent))
    return f"{percent:+d}%"
