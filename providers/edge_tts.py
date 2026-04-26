from __future__ import annotations

import io

import edge_tts

from config import base_voice_id
from providers.base import AbstractTTSProvider


class EdgeTTSProvider(AbstractTTSProvider):
    """Microsoft Edge TTS — free, supports Traditional Chinese."""

    async def synthesize(self, text: str, voice: str, **kwargs) -> bytes:
        speed = float(kwargs.get("speed", 1.0))
        rate = kwargs.get("rate") or _speed_to_rate(speed)
        pitch = str(kwargs.get("pitch", "+0Hz"))
        communicate = edge_tts.Communicate(text, base_voice_id(voice), rate=rate, pitch=pitch)
        buffer = io.BytesIO()
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                buffer.write(chunk["data"])
        buffer.seek(0)
        return buffer.read()


def _speed_to_rate(speed: float) -> str:
    percent = round((speed - 1.0) * 100)
    percent = max(-50, min(50, percent))
    return f"{percent:+d}%"
