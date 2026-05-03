from __future__ import annotations

from config import Provider
from backend.voice_catalog import list_voices, voice_provider as catalog_voice_provider


VOICE_CATALOG = list_voices()


def voice_provider(voice_id: str) -> Provider:
    return Provider(catalog_voice_provider(voice_id))
