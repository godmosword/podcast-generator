from __future__ import annotations

from abc import ABC, abstractmethod


class AbstractTTSProvider(ABC):
    @abstractmethod
    async def synthesize(self, text: str, voice: str, **kwargs) -> bytes:
        """Synthesize text to speech and return raw audio bytes (MP3)."""
        ...
