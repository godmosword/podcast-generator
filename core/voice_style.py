from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class VoiceStyle:
    pause_scale: float = 1.0


_SPEAKER_STYLES: dict[str, VoiceStyle] = {
    "主持人A": VoiceStyle(pause_scale=1.0),
    "主持人B": VoiceStyle(pause_scale=0.88),
    "主持人C": VoiceStyle(pause_scale=1.12),
    "主持人D": VoiceStyle(pause_scale=0.82),
    "主持人": VoiceStyle(pause_scale=1.0),
}

_DEFAULT = VoiceStyle()


def style_for(speaker: str) -> VoiceStyle:
    return _SPEAKER_STYLES.get(speaker, _DEFAULT)
