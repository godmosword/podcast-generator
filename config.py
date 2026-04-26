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
    "主持人D": "zh-CN-YunxiNeural",
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


@dataclass
class Config:
    provider: Provider = Provider(os.getenv("TTS_PROVIDER", "edge"))
    output_dir: Path = field(default_factory=lambda: Path(os.getenv("OUTPUT_DIR", "output")))
    bgm_path: str | None = os.getenv("BGM_PATH") or None
    bgm_volume_db: float = -20.0
    chunk_size: int = 4096
    segment_pause_ms: int = 500
    target_lufs: float = -16.0
    openai_api_key: str = field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    elevenlabs_api_key: str = field(default_factory=lambda: os.getenv("ELEVENLABS_API_KEY", ""))
    openai_model: str = "tts-1"
    concurrent_requests: int = 5

    def voice_map(self) -> dict[str, str]:
        if self.provider == Provider.OPENAI:
            return OPENAI_VOICE_MAP
        if self.provider == Provider.ELEVENLABS:
            return ELEVENLABS_VOICE_MAP
        return DEFAULT_VOICE_MAP

    def voice_for(self, speaker: str) -> str:
        mapping = self.voice_map()
        return mapping.get(speaker, mapping["_default"])
