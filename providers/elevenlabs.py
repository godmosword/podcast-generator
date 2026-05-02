from __future__ import annotations

import io

from elevenlabs import VoiceSettings
from elevenlabs.client import AsyncElevenLabs

from providers.base import AbstractTTSProvider


class ElevenLabsProvider(AbstractTTSProvider):
    """ElevenLabs TTS provider with conversational / narration voice style modes."""

    def __init__(self, api_key: str) -> None:
        self._client = AsyncElevenLabs(api_key=api_key)

    async def synthesize(self, text: str, voice: str, **kwargs) -> bytes:
        voice_mode = str(kwargs.get("voice_mode", "conversational"))

        if voice_mode == "conversational":
            default_stability = 0.35
            default_similarity = 0.75
            default_style = 0.45
            default_boost = True
        else:  # narration
            default_stability = 0.55
            default_similarity = 0.80
            default_style = 0.25
            default_boost = False

        stability = float(kwargs.get("stability", default_stability))
        similarity_boost = float(kwargs.get("similarity_boost", default_similarity))
        style = float(kwargs.get("style", default_style))
        use_speaker_boost = bool(kwargs.get("use_speaker_boost", default_boost))

        audio_stream = self._client.text_to_speech.convert(
            voice,
            text=text,
            voice_settings=VoiceSettings(
                stability=stability,
                similarity_boost=similarity_boost,
                style=style,
                use_speaker_boost=use_speaker_boost,
            ),
            model_id="eleven_multilingual_v2",
            output_format="mp3_44100_128",
        )

        buffer = io.BytesIO()
        async for chunk in audio_stream:
            buffer.write(chunk)
        buffer.seek(0)
        return buffer.read()
