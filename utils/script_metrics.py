from __future__ import annotations

import re
from dataclasses import dataclass

_SPEAKER_PREFIX_RE = re.compile(r"^\s*\[.+?\][:：]\s*", re.MULTILINE)
_PAUSE_DIRECTIVE_RE = re.compile(r"^\s*---PAUSE:\d+(?:\.\d+)?s---\s*$", re.MULTILINE)
_CJK_RE = re.compile(r"[\u4e00-\u9fff]")
_JAPANESE_RE = re.compile(r"[\u3040-\u30ff\u4e00-\u9fff]")
_WORD_RE = re.compile(r"[A-Za-z0-9]+(?:['-][A-Za-z0-9]+)?")


@dataclass(frozen=True)
class ScriptMetrics:
    unit_count: int
    unit_label: str
    unit_label_short: str
    target_per_minute: int
    estimated_duration_sec: int


def strip_script_markup(script: str) -> str:
    """Remove speaker tags and pause directives before measuring content length."""
    without_pauses = _PAUSE_DIRECTIVE_RE.sub("", script)
    return _SPEAKER_PREFIX_RE.sub("", without_pauses)


def target_units_for_duration(duration_min: int, language: str) -> tuple[int, str, str, int]:
    per_minute, label, short_label = _language_unit_config(language)
    return duration_min * per_minute, label, short_label, per_minute


def measure_script(script: str, language: str = "zh-TW") -> ScriptMetrics:
    content = strip_script_markup(script)
    per_minute, label, short_label = _language_unit_config(language)
    unit_count = _count_units(content, language)
    estimated = int(unit_count / per_minute * 60) if unit_count else 0
    return ScriptMetrics(
        unit_count=unit_count,
        unit_label=label,
        unit_label_short=short_label,
        target_per_minute=per_minute,
        estimated_duration_sec=estimated,
    )


def _language_unit_config(language: str) -> tuple[int, str, str]:
    if language == "en":
        return 150, "English words", "words"
    if language == "ja":
        return 300, "Japanese characters", "chars"
    return 200, "Chinese characters", "chars"


def _count_units(content: str, language: str) -> int:
    if language == "en":
        return len(_WORD_RE.findall(content))
    if language == "ja":
        return len(_JAPANESE_RE.findall(content))
    return len(_CJK_RE.findall(content))
