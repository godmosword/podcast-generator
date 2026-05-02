from __future__ import annotations

import io

from openai import AsyncOpenAI

from providers.base import AbstractTTSProvider


class OpenAITTSProvider(AbstractTTSProvider):
    """OpenAI TTS provider using the tts-1 or tts-1-hd model."""

    def __init__(self, api_key: str, model: str = "tts-1") -> None:
        self._client = AsyncOpenAI(api_key=api_key)
        self._model = model

    async def synthesize(self, text: str, voice: str, **kwargs) -> bytes:
        options = {}
        if "speed" in kwargs:
            options["speed"] = kwargs["speed"]

        response = await self._client.audio.speech.create(
            model=self._model,
            voice=voice,
            input=text,
            response_format="mp3",
            **options,
        )
        buffer = io.BytesIO()
        for chunk in response.iter_bytes():
            buffer.write(chunk)
        buffer.seek(0)
        return buffer.read()
