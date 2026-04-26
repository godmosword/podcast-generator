from __future__ import annotations

from pathlib import Path
from typing import Awaitable, Callable

from pydub import AudioSegment

from config import Config, Provider
from core.audio_processor import fade_edges, limit_peaks, merge_segments, mix_bgm, normalize_volume
from core.exporter import export_audio
from core.role_mapper import map_roles_to_voices
from core.script_parser import parse_script_details
from core.tts_engine import TTSEngine
from providers.base import AbstractTTSProvider
from providers.edge_tts import EdgeTTSProvider
from utils.file_utils import ensure_dir, read_text
from utils.text_chunker import chunk_text

ProgressCallback = Callable[[str, int, str], Awaitable[None]]


def _build_provider(config: Config) -> AbstractTTSProvider:
    if config.provider == Provider.EDGE:
        return EdgeTTSProvider()
    if config.provider == Provider.OPENAI:
        from providers.openai_tts import OpenAITTSProvider
        return OpenAITTSProvider(api_key=config.openai_api_key, model=config.openai_model)
    if config.provider == Provider.ELEVENLABS:
        from providers.elevenlabs import ElevenLabsProvider
        return ElevenLabsProvider(api_key=config.elevenlabs_api_key)
    raise ValueError(f"Unknown provider: {config.provider}")


class PodcastPipeline:
    def __init__(self, config: Config) -> None:
        self._config = config
        provider = _build_provider(config)
        self._engine = TTSEngine(provider, max_concurrent=config.concurrent_requests)

    async def run(
        self,
        script_path: str,
        output_path: str,
        metadata: dict | None = None,
        voice_overrides: dict[str, str] | None = None,
        output_format: str = "mp3",
        normalize: bool = True,
        bgm_enabled: bool = True,
        bgm_path: str | None = None,
        bgm_volume_db: float | None = None,
        bgm_fade_ms: int = 1500,
        progress: ProgressCallback | None = None,
    ) -> str:
        raw = read_text(script_path)
        return await self.run_text(
            raw,
            output_path,
            metadata=metadata,
            voice_overrides=voice_overrides,
            output_format=output_format,
            normalize=normalize,
            bgm_enabled=bgm_enabled,
            bgm_path=bgm_path,
            bgm_volume_db=bgm_volume_db,
            bgm_fade_ms=bgm_fade_ms,
            progress=progress,
        )

    async def run_text(
        self,
        script: str,
        output_path: str,
        metadata: dict | None = None,
        voice_overrides: dict[str, str] | None = None,
        output_format: str = "mp3",
        normalize: bool = True,
        bgm_enabled: bool = True,
        bgm_path: str | None = None,
        bgm_volume_db: float | None = None,
        bgm_fade_ms: int = 1500,
        progress: ProgressCallback | None = None,
    ) -> str:
        config = self._config
        parsed = parse_script_details(script)
        segments = parsed.turns

        if not segments:
            raise ValueError("No parseable content found in script.")

        voice_map = map_roles_to_voices(parsed.speakers, config, overrides=voice_overrides)

        print(f"  Parsed {len(segments)} segments from script.")
        await _emit(progress, "parsing", 10, f"Parsed {len(segments)} segments.")

        combined = AudioSegment.empty()
        speech_segments = [segment for segment in segments if not segment.is_silence]

        for i, segment in enumerate(segments):
            if segment.is_silence:
                combined = combined + AudioSegment.silent(duration=segment.pause_after_ms)
                continue

            voice = voice_map.get(segment.speaker, config.voice_for(segment.speaker))
            chunks = chunk_text(segment.text, max_chars=config.chunk_size)
            print(f"  [{i+1}/{len(segments)}] {segment.speaker} ({len(chunks)} chunk(s), voice={voice})")
            synthesized_count = len([item for item in segments[: i + 1] if not item.is_silence])
            pct = 10 + int((synthesized_count / max(1, len(speech_segments))) * 65)
            await _emit(progress, "synthesizing", pct, f"Synthesizing {segment.speaker}.")

            audio_chunks = await self._engine.synthesize_chunks(chunks, voice)
            segment_audio = merge_segments(audio_chunks, pause_ms=config.segment_pause_ms)

            combined = combined + segment_audio

            if segment.pause_after_ms:
                combined = combined + AudioSegment.silent(duration=segment.pause_after_ms)

        await _emit(progress, "mixing", 80, "Post-processing audio.")
        if normalize:
            combined = normalize_volume(combined, target_lufs=config.target_lufs)
        combined = limit_peaks(combined)
        combined = fade_edges(combined)

        effective_bgm_path = bgm_path or config.bgm_path
        effective_bgm_volume_db = config.bgm_volume_db if bgm_volume_db is None else bgm_volume_db
        if bgm_enabled and effective_bgm_path:
            print(f"  Mixing BGM from {effective_bgm_path}")
            combined = mix_bgm(
                combined,
                effective_bgm_path,
                bgm_volume_db=effective_bgm_volume_db,
                fade_ms=bgm_fade_ms,
            )
            combined = limit_peaks(combined)

        ensure_dir(Path(output_path).parent)
        await _emit(progress, "exporting", 92, f"Exporting {output_format.upper()}.")
        result = export_audio(combined, output_path, metadata=metadata, output_format=output_format)
        print(f"  Exported: {result}")
        await _emit(progress, "done", 100, "Export complete.")
        return result


async def _emit(progress: ProgressCallback | None, status: str, percent: int, message: str) -> None:
    if progress:
        await progress(status, percent, message)
