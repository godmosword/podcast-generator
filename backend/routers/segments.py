from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from backend.models.schemas import SegmentRegenerateResponse, SegmentResponse
from backend.projects import get_project
from backend.segments import get_segment, get_segments, synthesize_segment, update_segment_audio

router = APIRouter(prefix="/api/segments", tags=["segments"])


def _to_response(seg: dict) -> SegmentResponse:
    audio_url = f"/api/segments/{seg['id']}/audio" if seg.get("audio_path") else None
    return SegmentResponse(
        id=seg["id"],
        project_id=seg["project_id"],
        job_id=seg.get("job_id"),
        index=seg["index"],
        speaker=seg["speaker"],
        text=seg["text"],
        start_ms=seg["start_ms"],
        end_ms=seg["end_ms"],
        audio_url=audio_url,
        created_at=seg.get("created_at"),
    )


@router.get("/project/{project_id}", response_model=list[SegmentResponse])
async def get_timeline(project_id: str) -> list[SegmentResponse]:
    return [_to_response(s) for s in get_segments(project_id)]


@router.get("/{segment_id}/audio", response_model=None)
async def get_segment_audio(segment_id: str) -> FileResponse:
    seg = get_segment(segment_id)
    if not seg:
        raise HTTPException(status_code=404, detail="Segment not found.")
    audio_path = seg.get("audio_path")
    if not audio_path or not Path(audio_path).exists():
        raise HTTPException(status_code=404, detail="Segment audio file not found.")
    return FileResponse(audio_path, media_type="audio/mpeg", filename=Path(audio_path).name)


@router.post("/{segment_id}/regenerate", response_model=SegmentRegenerateResponse)
async def regenerate_segment(segment_id: str) -> SegmentRegenerateResponse:
    seg = get_segment(segment_id)
    if not seg:
        raise HTTPException(status_code=404, detail="Segment not found.")

    project = get_project(seg["project_id"])
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")

    voice_map: dict = project.get("voice_map") or {}
    speaker_settings: dict = project.get("speaker_settings") or {}
    speaker = seg["speaker"]

    from config import Config
    config = Config()
    voice_id: str = voice_map.get(speaker) or config.voice_for(speaker)

    audio = await synthesize_segment(
        text=seg["text"],
        voice_id=voice_id,
        speaker=speaker,
        speaker_settings=speaker_settings or None,
    )

    dest = Path("output/segments") / seg["project_id"] / f"{segment_id}_regen.mp3"
    dest.parent.mkdir(parents=True, exist_ok=True)
    audio.export(str(dest), format="mp3", bitrate="128k")

    update_segment_audio(segment_id, str(dest))

    return SegmentRegenerateResponse(
        segment_id=segment_id,
        audio_url=f"/api/segments/{segment_id}/audio",
        duration_ms=len(audio),
    )
