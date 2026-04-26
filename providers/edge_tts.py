from __future__ import annotations

import io

import edge_tts

from providers.base import AbstractTTSProvider


class EdgeTTSProvider(AbstractTTSProvider):
    """Microsoft Edge TTS — free, supports Traditional Chinese."""

    async def synthesize(self, text: str, voice: str, **kwargs) -> bytes:
        communicate = edge_tts.Communicate(text, voice)
        buffer = io.BytesIO()
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                buffer.write(chunk["data"])
        buffer.seek(0)
        return buffer.read()
