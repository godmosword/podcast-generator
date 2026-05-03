from __future__ import annotations

import os
from dataclasses import dataclass, field
from enum import Enum
from ipaddress import ip_network
from pathlib import Path

from dotenv import load_dotenv

from backend.voice_catalog import provider_voice_id, tts_options_for

load_dotenv()


class Provider(str, Enum):
    EDGE = "edge"
    OPENAI = "openai"
    ELEVENLABS = "elevenlabs"


DEFAULT_VOICE_MAP: dict[str, str] = {
    "主持人": "edge:zh-TW-HsiaoChenNeural",
    "主持人A": "edge:zh-TW-HsiaoChenNeural",
    "主持人B": "edge:zh-TW-YunJheNeural",
    "主持人C": "edge:zh-TW-HsiaoYuNeural",
    "主持人D": "edge:zh-TW-YunJheNeural__adult-male-2",
    "來賓": "edge:zh-TW-YunJheNeural",
    "narrator": "edge:zh-TW-HsiaoChenNeural",
    "speaker_1": "edge:zh-TW-HsiaoChenNeural",
    "_default": "edge:zh-TW-HsiaoChenNeural",
}

OPENAI_VOICE_MAP: dict[str, str] = {
    "主持人": "openai:nova",
    "主持人A": "openai:nova",
    "主持人B": "openai:echo",
    "主持人C": "openai:alloy",
    "主持人D": "openai:fable",
    "來賓": "openai:echo",
    "narrator": "openai:alloy",
    "speaker_1": "openai:nova",
    "_default": "openai:alloy",
}

ELEVENLABS_VOICE_MAP: dict[str, str] = {
    "主持人": "elevenlabs:Rachel",
    "來賓": "elevenlabs:Adam",
    "narrator": "elevenlabs:Rachel",
    "_default": "elevenlabs:Rachel",
}


def _env_list(name: str, default: str) -> list[str]:
    raw = os.getenv(name, default)
    values = [item.strip() for item in raw.split(",") if item.strip()]
    return values


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return default
    return int(raw)


@dataclass
class Config:
    app_env: str = field(default_factory=lambda: os.getenv("APP_ENV", "development"))
    provider: Provider = field(default_factory=lambda: Provider(os.getenv("TTS_PROVIDER", "edge")))
    output_dir: Path = field(default_factory=lambda: Path(os.getenv("OUTPUT_DIR", "output")))
    bgm_path: str | None = os.getenv("BGM_PATH") or None
    bgm_volume_db: float = -20.0
    chunk_size: int = 4096
    segment_pause_ms: int = 500
    target_lufs: float = -16.0
    speech_speed: float = 1.12
    openai_api_key: str = field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    elevenlabs_api_key: str = field(default_factory=lambda: os.getenv("ELEVENLABS_API_KEY", ""))
    gemini_api_key: str = field(default_factory=lambda: os.getenv("GEMINI_API_KEY", ""))
    gemini_model: str = field(default_factory=lambda: os.getenv("GEMINI_MODEL", "gemini-3-flash-preview"))
    openai_model: str = "tts-1"
    concurrent_requests: int = 5
    voice_mode: str = "conversational"
    voice_quality: str = "standard"
    cors_origins: list[str] = field(default_factory=lambda: _env_list("CORS_ORIGINS", "http://localhost:3000"))
    trust_proxy_headers: bool = field(default_factory=lambda: _env_bool("TRUST_PROXY_HEADERS", False))
    trusted_proxy_cidrs: list[str] = field(default_factory=lambda: _env_list("TRUSTED_PROXY_CIDRS", ""))
    rate_limit_generate_per_minute: int = field(default_factory=lambda: _env_int("RATE_LIMIT_GENERATE_PER_MINUTE", 5))
    rate_limit_preview_per_minute: int = field(default_factory=lambda: _env_int("RATE_LIMIT_PREVIEW_PER_MINUTE", 20))
    rate_limit_ai_per_minute: int = field(default_factory=lambda: _env_int("RATE_LIMIT_AI_PER_MINUTE", 10))

    def __post_init__(self) -> None:
        self.app_env = self.app_env.strip().lower()
        if self.app_env == "production" and (not self.cors_origins or "*" in self.cors_origins):
            raise ValueError("CORS_ORIGINS must be configured with explicit origins when APP_ENV=production.")

        for cidr in self.trusted_proxy_cidrs:
            ip_network(cidr, strict=False)

        for name, value in {
            "RATE_LIMIT_GENERATE_PER_MINUTE": self.rate_limit_generate_per_minute,
            "RATE_LIMIT_PREVIEW_PER_MINUTE": self.rate_limit_preview_per_minute,
            "RATE_LIMIT_AI_PER_MINUTE": self.rate_limit_ai_per_minute,
        }.items():
            if value <= 0:
                raise ValueError(f"{name} must be greater than 0.")

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
        catalog_options = tts_options_for(voice)
        if self.provider == Provider.OPENAI:
            return {**catalog_options, "speed": self.speech_speed, "provider_voice_id": provider_voice_id(voice)}
        if self.provider == Provider.ELEVENLABS:
            return {"voice_mode": self.voice_mode, **catalog_options, "provider_voice_id": provider_voice_id(voice)}
        return {**catalog_options, "speed": self.speech_speed, "pitch": voice_pitch(voice), "provider_voice_id": provider_voice_id(voice)}


def base_voice_id(voice: str) -> str:
    return provider_voice_id(voice).split("__", 1)[0]


def voice_pitch(voice: str) -> str:
    options = tts_options_for(voice)
    if "pitch" in options:
        return str(options["pitch"])
    profile = voice.split("__", 1)[1] if "__" in voice else ""
    profile_pitch = {
        "adult-male-2": "-2Hz",
        "adult-female-2": "+1Hz",
        "boy-1": "+85Hz",
        "boy-2": "+100Hz",
        "girl-1": "+90Hz",
        "girl-2": "+100Hz",
    }
    return profile_pitch.get(profile, "+0Hz")
