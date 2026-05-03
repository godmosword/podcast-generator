from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
import uuid

from backend.models.database import Project, SessionLocal


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _to_dict(project: Project) -> dict[str, Any]:
    return {
        "id": project.id,
        "title": project.title,
        "script": project.script,
        "hosts": project.hosts or [],
        "voice_map": project.voice_map or {},
        "bgm_id": project.bgm_id,
        "speaker_settings": project.speaker_settings or {},
        "last_generated_job_id": project.last_generated_job_id,
        "created_at": project.created_at.isoformat() if project.created_at else None,
        "updated_at": project.updated_at.isoformat() if project.updated_at else None,
    }


def create_project(
    title: str = "未命名 Podcast",
    script: str = "",
    hosts: list | None = None,
    voice_map: dict | None = None,
    bgm_id: str | None = None,
    speaker_settings: dict | None = None,
) -> dict[str, Any]:
    project_id = f"proj_{uuid.uuid4().hex[:12]}"
    now = _now()
    with SessionLocal() as db:
        project = Project(
            id=project_id,
            title=title,
            script=script,
            hosts=hosts or [],
            voice_map=voice_map or {},
            bgm_id=bgm_id,
            speaker_settings=speaker_settings or {},
            created_at=now,
            updated_at=now,
        )
        db.add(project)
        db.commit()
        return _to_dict(project)


def get_project(project_id: str) -> dict[str, Any] | None:
    with SessionLocal() as db:
        project = db.get(Project, project_id)
        if project is None:
            return None
        return _to_dict(project)


def update_project(project_id: str, **kwargs: Any) -> dict[str, Any] | None:
    _ALLOWED = {"title", "script", "hosts", "voice_map", "bgm_id", "speaker_settings", "last_generated_job_id"}
    with SessionLocal() as db:
        project = db.get(Project, project_id)
        if project is None:
            return None
        for key, value in kwargs.items():
            if key in _ALLOWED:
                setattr(project, key, value)
        project.updated_at = _now()
        db.commit()
        return _to_dict(project)


def list_projects(limit: int = 50) -> list[dict[str, Any]]:
    with SessionLocal() as db:
        projects = (
            db.query(Project)
            .order_by(Project.updated_at.desc())
            .limit(limit)
            .all()
        )
        return [_to_dict(p) for p in projects]
