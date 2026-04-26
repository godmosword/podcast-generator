from __future__ import annotations

import io

from elevenlabs.client import AsyncElevenLabs

from providers.base import AbstractTTSProvider


class ElevenLabsProvider(AbstractTTSProvider):
    """ElevenLabs TTS provider with voice stability and similarity control."""

    def __init__(self, api_key: str) -> None:
        self._client = AsyncElevenLabs(api_key=api_key)

    async def synthesize(self, text: str, voice: str, **kwargs) -> bytes:
        stability: float = kwargs.get("stability", 0.5)
        similarity_boost: float = kwargs.get("similarity_boost", 0.75)

        audio_stream = await self._client.generate(
            text=text,
            voice=voice,
            voice_settings={
                "stability": stability,
                "similarity_boost": similarity_boost,
            },
            model="eleven_multilingual_v2",
            output_format="mp3_44100_128",
        )

        buffer = io.BytesIO()
        async for chunk in audio_stream:
            buffer.write(chunk)
        buffer.seek(0)
        return buffer.read()
