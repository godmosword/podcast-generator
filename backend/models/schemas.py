from __future__ import annotations

import os
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

from backend.voice_catalog import is_known_voice


OutputFormat = Literal["mp3", "wav"]
JobStatus = Literal["queued", "parsing", "synthesizing", "mixing", "exporting", "done", "failed"]
def validate_voice_id(value: str) -> str:
    if value.startswith("elevenlabs:") and len(value) > len("elevenlabs:"):
        return value
    if not is_known_voice(value):
        raise ValueError(f"Unknown voice: {value}")
    return value


class VoiceAssignment(BaseModel):
    role: str = Field(min_length=1, max_length=80)
    voice: str = Field(min_length=1, max_length=120)

    @field_validator("voice")
    @classmethod
    def voice_must_be_known(cls, value: str) -> str:
        return validate_voice_id(value)


class SpeakerAudioSettings(BaseModel):
    volume_db: float = Field(default=0.0, ge=-12.0, le=12.0)
    eq_preset: Literal["chat", "news", "story"] = "chat"


class AudioSettings(BaseModel):
    speed: float = Field(default=1.0, ge=0.75, le=1.35)
    pause_ms: int = Field(default=500, ge=100, le=1200)
    bgm_enabled: bool = True
    bgm_id: str | None = Field(default=None, max_length=120)
    bgm_volume_db: float = Field(default=-20.0, ge=-36.0, le=-6.0)
    bgm_fade_ms: int = Field(default=1500, ge=0, le=8000)
    output_format: OutputFormat = "mp3"
    normalize: bool = True
    voice_mode: Literal["conversational", "narration"] = "conversational"
    voice_quality: Literal["standard", "high"] = "standard"
    post_process: bool = False


class GenerateRequest(BaseModel):
    script: str = Field(min_length=1)

    @field_validator("script")
    @classmethod
    def check_script_length(cls, v: str) -> str:
        max_len = int(os.getenv("MAX_SCRIPT_LENGTH", "50000"))
        if len(v) > max_len:
            raise ValueError(f"腳本超過字數上限（{max_len} 字）。")
        return v
    host_count: int = Field(default=1, ge=1, le=4)
    voice_assignments: list[VoiceAssignment] = Field(default_factory=list, max_length=4)
    audio: AudioSettings = Field(default_factory=AudioSettings)
    speaker_settings: dict[str, SpeakerAudioSettings] = Field(default_factory=dict)
    project_id: str | None = Field(default=None, max_length=80)
    title: str | None = Field(default=None, max_length=200)
    artist: str | None = Field(default=None, max_length=200)
    album: str | None = Field(default=None, max_length=200)


class GenerateResponse(BaseModel):
    job_id: str
    events_url: str
    file_url: str | None = None


class PreviewRequest(BaseModel):
    text: str = Field(min_length=1, max_length=500)
    voice: str = Field(min_length=1, max_length=120)
    seconds: int = Field(default=15, ge=1, le=15)

    @field_validator("voice")
    @classmethod
    def voice_must_be_known(cls, value: str) -> str:
        return validate_voice_id(value)


class JobSnapshot(BaseModel):
    id: str
    status: JobStatus
    progress: int
    message: str
    file_url: str | None = None
    error: str | None = None
    retry_count: int = 0
    last_provider: str | None = None


class ProjectCreate(BaseModel):
    title: str = Field(default="未命名 Podcast", max_length=200)
    script: str = Field(default="", max_length=50000)
    hosts: list[dict[str, Any]] = Field(default_factory=list)
    voice_map: dict[str, str] = Field(default_factory=dict)
    bgm_id: str | None = Field(default=None, max_length=120)
    speaker_settings: dict[str, dict[str, Any]] = Field(default_factory=dict)


class ProjectUpdate(BaseModel):
    title: str | None = Field(default=None, max_length=200)
    script: str | None = Field(default=None, max_length=50000)
    hosts: list[dict[str, Any]] | None = None
    voice_map: dict[str, str] | None = None
    bgm_id: str | None = None
    speaker_settings: dict[str, dict[str, Any]] | None = None


class ProjectResponse(BaseModel):
    id: str
    title: str
    script: str
    hosts: list[dict[str, Any]]
    voice_map: dict[str, str]
    bgm_id: str | None
    speaker_settings: dict[str, dict[str, Any]]
    last_generated_job_id: str | None
    chapters: list[dict[str, Any]]
    show_notes: str
    created_at: str | None
    updated_at: str | None


class ProjectSummary(BaseModel):
    id: str
    title: str
    last_generated_job_id: str | None
    updated_at: str | None


class SegmentResponse(BaseModel):
    id: str
    project_id: str
    job_id: str | None
    index: int
    speaker: str
    text: str
    start_ms: int
    end_ms: int
    audio_url: str | None
    created_at: str | None


class SegmentRegenerateResponse(BaseModel):
    segment_id: str
    audio_url: str
    duration_ms: int
