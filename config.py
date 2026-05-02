from __future__ import annotations

import os
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


class Provider(str, Enum):
    EDGE = "edge"
    OPENAI = "openai"
    ELEVENLABS = "elevenlabs"


DEFAULT_VOICE_MAP: dict[str, str] = {
    "主持人": "zh-TW-HsiaoChenNeural",
    "主持人A": "zh-TW-HsiaoChenNeural",
    "主持人B": "zh-TW-YunJheNeural",
    "主持人C": "zh-TW-HsiaoYuNeural",
    "主持人D": "zh-TW-YunJheNeural__adult-male-2",
    "來賓": "zh-TW-YunJheNeural",
    "narrator": "zh-TW-HsiaoChenNeural",
    "speaker_1": "zh-TW-HsiaoChenNeural",
    "_default": "zh-TW-HsiaoChenNeural",
}

OPENAI_VOICE_MAP: dict[str, str] = {
    "主持人": "nova",
    "來賓": "echo",
    "narrator": "alloy",
    "_default": "alloy",
}

ELEVENLABS_VOICE_MAP: dict[str, str] = {
    "主持人": "Rachel",
    "來賓": "Adam",
    "narrator": "Rachel",
    "_default": "Rachel",
}


def _env_list(name: str, default: str) -> list[str]:
    raw = os.getenv(name, default)
    values = [item.strip() for item in raw.split(",") if item.strip()]
    return values or [default]


@dataclass
class Config:
    provider: Provider = Provider(os.getenv("TTS_PROVIDER", "edge"))
    output_dir: Path = field(default_factory=lambda: Path(os.getenv("OUTPUT_DIR", "output")))
    bgm_path: str | None = os.getenv("BGM_PATH") or None
    bgm_volume_db: float = -20.0
    chunk_size: int = 4096
    segment_pause_ms: int = 500
    target_lufs: float = -16.0
    speech_speed: float = 1.06
    openai_api_key: str = field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    elevenlabs_api_key: str = field(default_factory=lambda: os.getenv("ELEVENLABS_API_KEY", ""))
    anthropic_api_key: str = field(default_factory=lambda: os.getenv("ANTHROPIC_API_KEY", ""))
    openai_model: str = "tts-1"
    concurrent_requests: int = 5
    voice_mode: str = "conversational"
    voice_quality: str = "standard"
    cors_origins: list[str] = field(default_factory=lambda: _env_list("CORS_ORIGINS", "*"))

    def voice_map(self) -> dict[str, str]:
        if self.provider == Provider.OPENAI:
            return OPENAI_VOICE_MAP
        if self.provider == Provider.ELEVENLABS:
            return ELEVENLABS_VOICE_MAP
        return DEFAULT_VOICE_MAP

    def voice_for(self, speaker: str) -> str:
        mapping = self.voice_map()
        return mapping.get(speaker, mapping["_default"])

    def tts_options_for(self, voice: str) -> dict[str, float | str]:
        if self.provider == Provider.OPENAI:
            return {"speed": self.speech_speed}
        if self.provider == Provider.ELEVENLABS:
            return {"voice_mode": self.voice_mode}
        return {"speed": self.speech_speed, "pitch": voice_pitch(voice)}


def base_voice_id(voice: str) -> str:
    return voice.split("__", 1)[0]


def voice_pitch(voice: str) -> str:
    profile = voice.split("__", 1)[1] if "__" in voice else ""
    profile_pitch = {
        "adult-male-2": "-2Hz",
        "adult-female-2": "+1Hz",
        "boy-1": "+22Hz",
        "boy-2": "+26Hz",
        "girl-1": "+28Hz",
        "girl-2": "+32Hz",
    }
    return profile_pitch.get(profile, "+0Hz")
