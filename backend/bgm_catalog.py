from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pydub import AudioSegment

SUPPORTED_BGM_EXTENSIONS = {".mp3", ".wav"}
DEFAULT_BGM_DIR = Path("assets/bgm")
USER_BGM_DIR = Path("output/user_bgm")


class BgmNotFoundError(ValueError):
    pass


@dataclass(frozen=True)
class BgmTrack:
    id: str
    title: str
    mood: str
    duration: float
    path: Path

    @property
    def preview_url(self) -> str:
        return f"/api/bgm/{self.id}/preview"

    def to_public_dict(self) -> dict[str, str | float]:
        return {
            "id": self.id,
            "title": self.title,
            "mood": self.mood,
            "duration": self.duration,
            "preview_url": self.preview_url,
        }


def list_bgm_tracks(bgm_dir: Path = DEFAULT_BGM_DIR) -> list[BgmTrack]:
    bgm_dir = Path(bgm_dir)
    manifest_entries = _load_manifest(bgm_dir)
    tracks: list[BgmTrack] = []
    seen_paths: set[Path] = set()

    for entry in manifest_entries:
        filename = str(entry.get("filename") or "")
        if not filename:
            continue
        path = (bgm_dir / filename).resolve()
        if not _is_supported_audio(path) or not path.exists():
            continue
        seen_paths.add(path)
        tracks.append(
            BgmTrack(
                id=str(entry.get("id") or path.stem),
                title=str(entry.get("title") or path.stem.replace("-", " ").title()),
                mood=str(entry.get("mood") or "general"),
                duration=float(entry.get("duration") or _duration_seconds(path)),
                path=path,
            )
        )

    if bgm_dir.exists():
        for path in sorted(bgm_dir.iterdir()):
            resolved = path.resolve()
            if resolved in seen_paths or not _is_supported_audio(path):
                continue
            tracks.append(
                BgmTrack(
                    id=path.stem,
                    title=path.stem.replace("-", " ").replace("_", " ").title(),
                    mood="general",
                    duration=_duration_seconds(path),
                    path=resolved,
                )
            )

    # Append user-uploaded BGM tracks.
    for path in sorted(USER_BGM_DIR.iterdir()) if USER_BGM_DIR.exists() else []:
        if not _is_supported_audio(path):
            continue
        resolved = path.resolve()
        if resolved in seen_paths:
            continue
        seen_paths.add(resolved)
        tracks.append(
            BgmTrack(
                id=path.stem,
                title=path.stem.replace("-", " ").replace("_", " ").title(),
                mood="custom",
                duration=_duration_seconds(path),
                path=resolved,
            )
        )

    return tracks


def get_bgm_track(track_id: str, bgm_dir: Path = DEFAULT_BGM_DIR) -> BgmTrack:
    for track in list_bgm_tracks(bgm_dir):
        if track.id == track_id:
            return track
    raise BgmNotFoundError(f"Unknown BGM track: {track_id}")


def _load_manifest(bgm_dir: Path) -> list[dict[str, Any]]:
    manifest_path = bgm_dir / "manifest.json"
    if not manifest_path.exists():
        return []
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        return []
    return [entry for entry in data if isinstance(entry, dict)]


def _is_supported_audio(path: Path) -> bool:
    return path.suffix.lower() in SUPPORTED_BGM_EXTENSIONS


def _duration_seconds(path: Path) -> float:
    try:
        return round(len(AudioSegment.from_file(path)) / 1000, 2)
    except Exception:
        return 0.0
