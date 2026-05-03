from __future__ import annotations

import io
import shutil
import uuid
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile
from fastapi.responses import FileResponse, StreamingResponse
from pydub import AudioSegment

from backend.bgm_catalog import SUPPORTED_BGM_EXTENSIONS, USER_BGM_DIR, BgmNotFoundError, get_bgm_track, list_bgm_tracks

router = APIRouter(prefix="/api", tags=["bgm"])


@router.get("/bgm")
async def bgm_catalog() -> list[dict[str, str | float]]:
    return [track.to_public_dict() for track in list_bgm_tracks()]


@router.get("/bgm/{track_id}/preview", response_model=None)
async def bgm_preview(track_id: str) -> StreamingResponse | FileResponse:
    try:
        track = get_bgm_track(track_id)
    except BgmNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    try:
        audio = AudioSegment.from_file(track.path)[:30_000]
        buffer = io.BytesIO()
        audio.export(buffer, format="mp3", bitrate="128k")
        buffer.seek(0)
        return StreamingResponse(buffer, media_type="audio/mpeg")
    except Exception:
        media_type = "audio/wav" if track.path.suffix.lower() == ".wav" else "audio/mpeg"
        return FileResponse(track.path, media_type=media_type, filename=track.path.name)


@router.post("/bgm/upload")
async def upload_bgm(file: UploadFile) -> dict[str, str]:
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided.")
    suffix = Path(file.filename).suffix.lower()
    if suffix not in SUPPORTED_BGM_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Only MP3 and WAV files are supported.")

    USER_BGM_DIR.mkdir(parents=True, exist_ok=True)
    bgm_id = f"user_{uuid.uuid4().hex[:8]}"
    dest = USER_BGM_DIR / f"{bgm_id}{suffix}"

    with dest.open("wb") as out:
        shutil.copyfileobj(file.file, out)

    return {"bgm_id": bgm_id, "name": file.filename}
