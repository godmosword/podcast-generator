from __future__ import annotations

import asyncio

from providers.base import AbstractTTSProvider


class TTSEngine:
    def __init__(self, provider: AbstractTTSProvider, max_concurrent: int = 5) -> None:
        self._provider = provider
        self._semaphore = asyncio.Semaphore(max_concurrent)

    async def synthesize(self, text: str, voice: str, **kwargs) -> bytes:
        async with self._semaphore:
            return await self._provider.synthesize(text, voice, **kwargs)

    async def synthesize_chunks(self, chunks: list[str], voice: str) -> list[bytes]:
        """Synthesize all chunks concurrently (bounded by semaphore)."""
        tasks = [self.synthesize(chunk, voice) for chunk in chunks]
        return await asyncio.gather(*tasks)
