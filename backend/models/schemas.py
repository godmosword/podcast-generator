from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


OutputFormat = Literal["mp3", "wav"]
JobStatus = Literal["queued", "parsing", "synthesizing", "mixing", "exporting", "done", "failed"]


class VoiceAssignment(BaseModel):
    role: str = Field(min_length=1, max_length=80)
    voice: str = Field(min_length=1, max_length=120)


class AudioSettings(BaseModel):
    speed: float = Field(default=1.0, ge=0.75, le=1.35)
    pause_ms: int = Field(default=500, ge=100, le=1200)
    bgm_enabled: bool = True
    bgm_id: str | None = Field(default=None, max_length=120)
    bgm_volume_db: float = Field(default=-20.0, ge=-36.0, le=-6.0)
    bgm_fade_ms: int = Field(default=1500, ge=0, le=8000)
    output_format: OutputFormat = "mp3"
    normalize: bool = True


class GenerateRequest(BaseModel):
    script: str = Field(min_length=1)
    host_count: int = Field(default=1, ge=1, le=4)
    voice_assignments: list[VoiceAssignment] = Field(default_factory=list)
    audio: AudioSettings = Field(default_factory=AudioSettings)
    title: str | None = None
    artist: str | None = None
    album: str | None = None


class GenerateResponse(BaseModel):
    job_id: str
    events_url: str
    file_url: str | None = None


class PreviewRequest(BaseModel):
    text: str = Field(min_length=1, max_length=500)
    voice: str = Field(min_length=1, max_length=120)
    seconds: int = Field(default=15, ge=1, le=15)


class JobSnapshot(BaseModel):
    id: str
    status: JobStatus
    progress: int
    message: str
    file_url: str | None = None
    error: str | None = None
