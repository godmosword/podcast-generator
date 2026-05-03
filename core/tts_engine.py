from __future__ import annotations

import asyncio
import logging

from providers.base import AbstractTTSProvider

logger = logging.getLogger(__name__)

_MAX_ATTEMPTS = 3
_BACKOFF_BASE = 1.0  # seconds; doubles each retry: 1s, 2s


class TTSEngine:
    def __init__(self, provider: AbstractTTSProvider, max_concurrent: int = 5) -> None:
        self._provider = provider
        self._semaphore = asyncio.Semaphore(max_concurrent)

    async def synthesize(self, text: str, voice: str, **kwargs) -> bytes:
        last_exc: Exception | None = None
        for attempt in range(_MAX_ATTEMPTS):
            try:
                async with self._semaphore:
                    return await self._provider.synthesize(text, voice, **kwargs)
            except Exception as exc:
                last_exc = exc
                if attempt < _MAX_ATTEMPTS - 1:
                    wait = _BACKOFF_BASE * (2 ** attempt)
                    logger.warning(
                        "TTS attempt %d/%d failed (%s). Retrying in %.1fs.",
                        attempt + 1, _MAX_ATTEMPTS, exc, wait,
                    )
                    await asyncio.sleep(wait)
        raise last_exc  # type: ignore[misc]

    async def synthesize_chunks(self, chunks: list[str], voice: str, **kwargs) -> list[bytes]:
        """Synthesize all chunks concurrently (bounded by semaphore)."""
        tasks = [self.synthesize(chunk, voice, **kwargs) for chunk in chunks]
        return await asyncio.gather(*tasks)
