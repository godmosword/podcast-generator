from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from pydub import AudioSegment

from backend.models.database import Segment, SessionLocal


def _seg_to_dict(seg: Segment) -> dict[str, Any]:
    return {
        "id": seg.id,
        "project_id": seg.project_id,
        "job_id": seg.job_id,
        "index": seg.index,
        "speaker": seg.speaker,
        "text": seg.text,
        "start_ms": seg.start_ms,
        "end_ms": seg.end_ms,
        "audio_path": seg.audio_path,
        "created_at": seg.created_at.isoformat() if seg.created_at else None,
    }


def upsert_segments(project_id: str, job_id: str, segments_data: list[dict[str, Any]]) -> None:
    with SessionLocal() as db:
        db.query(Segment).filter(Segment.project_id == project_id).delete()
        now = datetime.now(timezone.utc)
        for seg in segments_data:
            db.add(Segment(
                id=f"seg_{uuid.uuid4().hex[:10]}",
                project_id=project_id,
                job_id=job_id,
                index=seg["index"],
                speaker=seg["speaker"],
                text=seg["text"],
                start_ms=seg["start_ms"],
                end_ms=seg["end_ms"],
                audio_path=seg.get("audio_path"),
                created_at=now,
            ))
        db.commit()


def get_segments(project_id: str) -> list[dict[str, Any]]:
    with SessionLocal() as db:
        segs = (
            db.query(Segment)
            .filter(Segment.project_id == project_id)
            .order_by(Segment.index)
            .all()
        )
        return [_seg_to_dict(s) for s in segs]


def get_segment(segment_id: str) -> dict[str, Any] | None:
    with SessionLocal() as db:
        seg = db.get(Segment, segment_id)
        return _seg_to_dict(seg) if seg else None


def update_segment_audio(segment_id: str, audio_path: str) -> None:
    with SessionLocal() as db:
        seg = db.get(Segment, segment_id)
        if seg:
            seg.audio_path = audio_path
            db.commit()


async def synthesize_segment(
    text: str,
    voice_id: str,
    speaker: str,
    speaker_settings: dict | None,
) -> AudioSegment:
    """Re-synthesize a single segment and return its AudioSegment."""
    from config import Config
    from backend.config import voice_provider
    from pipeline.podcast_pipeline import _build_provider
    from core.tts_engine import TTSEngine
    from core.audio_processor import merge_segments, apply_per_speaker_settings
    from core.voice_style import style_for
    from utils.text_chunker import chunk_text
    from backend.utils.text_preprocessor import preprocess_for_tts

    config = Config()
    config.provider = voice_provider(voice_id)

    provider = _build_provider(config)
    engine = TTSEngine(provider, max_concurrent=1)
    style = style_for(speaker)
    chunks = chunk_text(preprocess_for_tts(text), max_chars=config.chunk_size)
    options = {**config.tts_options_for(voice_id), "pause_scale": style.pause_scale}
    audio_chunks = await engine.synthesize_chunks(chunks, voice_id, **options)
    audio = merge_segments(audio_chunks, pause_ms=config.segment_pause_ms)
    if speaker_settings:
        audio = apply_per_speaker_settings(audio, speaker, speaker_settings)
    return audio
