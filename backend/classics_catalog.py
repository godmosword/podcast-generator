from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

DEFAULT_CLASSICS_DIR = Path("assets/classics")

DurationCategory = Literal["short", "medium", "long"]


class ClassicNotFoundError(ValueError):
    pass


@dataclass(frozen=True)
class ClassicEntry:
    id: str
    title: str
    author: str
    category: str
    duration_category: str
    duration_minutes: int
    language: str
    description: str
    speaker_count: int
    tags: list[str]
    script_path: Path

    def to_public_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "author": self.author,
            "category": self.category,
            "duration_category": self.duration_category,
            "duration_minutes": self.duration_minutes,
            "language": self.language,
            "description": self.description,
            "speaker_count": self.speaker_count,
            "tags": self.tags,
        }


def list_classics(
    classics_dir: Path = DEFAULT_CLASSICS_DIR,
    duration_category: DurationCategory | None = None,
) -> list[ClassicEntry]:
    classics_dir = Path(classics_dir)
    results: list[ClassicEntry] = []
    for entry in _load_manifest(classics_dir):
        classic = _build_entry(entry, classics_dir)
        if classic is None:
            continue
        if duration_category and classic.duration_category != duration_category:
            continue
        results.append(classic)
    return results


def get_classic(classic_id: str, classics_dir: Path = DEFAULT_CLASSICS_DIR) -> ClassicEntry:
    for classic in list_classics(classics_dir):
        if classic.id == classic_id:
            return classic
    raise ClassicNotFoundError(f"Unknown classic: {classic_id}")


def get_classic_script(classic_id: str, classics_dir: Path = DEFAULT_CLASSICS_DIR) -> str:
    classic = get_classic(classic_id, classics_dir)
    if not classic.script_path.exists():
        raise ClassicNotFoundError(f"Script file missing for: {classic_id}")
    return classic.script_path.read_text(encoding="utf-8")


def _build_entry(entry: dict[str, Any], classics_dir: Path) -> ClassicEntry | None:
    entry_id = str(entry.get("id") or "")
    if not entry_id:
        return None
    script_path = (classics_dir / "scripts" / f"{entry_id}.txt").resolve()
    if not script_path.exists():
        return None
    return ClassicEntry(
        id=entry_id,
        title=str(entry.get("title") or entry_id),
        author=str(entry.get("author") or ""),
        category=str(entry.get("category") or "western-classic"),
        duration_category=str(entry.get("duration_category") or "short"),
        duration_minutes=int(entry.get("duration_minutes") or 0),
        language=str(entry.get("language") or "zh-TW"),
        description=str(entry.get("description") or ""),
        speaker_count=int(entry.get("speaker_count") or 2),
        tags=list(entry.get("tags") or []),
        script_path=script_path,
    )


def _load_manifest(classics_dir: Path) -> list[dict[str, Any]]:
    manifest_path = classics_dir / "manifest.json"
    if not manifest_path.exists():
        return []
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        return []
    return [e for e in data if isinstance(e, dict)]
