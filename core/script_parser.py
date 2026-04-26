from __future__ import annotations

import re
from dataclasses import dataclass

_SPEAKER_LINE = re.compile(r"^\[(.+?)\][:：]\s*(.+)$")
_PAUSE_DIRECTIVE = re.compile(r"^---PAUSE:(\d+(?:\.\d+)?)s---$")
_MARKDOWN_STRIP = re.compile(r"[*_`#>]+")


@dataclass
class ScriptSegment:
    speaker: str
    text: str
    index: int = 0
    pause_after_ms: int = 0
    is_silence: bool = False

    @classmethod
    def silence(cls, duration_ms: int, index: int = 0) -> "ScriptSegment":
        return cls(speaker="", text="", index=index, pause_after_ms=duration_ms, is_silence=True)


@dataclass
class ParsedScript:
    turns: list[ScriptSegment]
    speakers: list[str]
    speaker_count: int


def parse_script(raw: str, default_speaker: str = "narrator") -> list[ScriptSegment]:
    """Parse a script into segments.

    Supports:
      [Speaker]: text          — labelled speaker line
      ---PAUSE:1.5s---         — explicit silence directive
      plain text               — assigned to default_speaker
    """
    return parse_script_details(raw, default_speaker=default_speaker).turns


def parse_script_details(raw: str, default_speaker: str = "speaker_1") -> ParsedScript:
    """Parse a script and include speaker metadata for API/UI workflows."""
    segments: list[ScriptSegment] = []
    lines = raw.splitlines()
    has_speaker_tags = any(_SPEAKER_LINE.match(line.strip()) for line in lines)
    fallback_speaker = default_speaker if not has_speaker_tags else "narrator"

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        pause_match = _PAUSE_DIRECTIVE.match(stripped)
        if pause_match:
            ms = int(float(pause_match.group(1)) * 1000)
            segments.append(ScriptSegment.silence(ms, index=len(segments)))
            continue

        speaker_match = _SPEAKER_LINE.match(stripped)
        if speaker_match:
            speaker = speaker_match.group(1).strip()
            text = _clean_text(speaker_match.group(2).strip())
            if text:
                segments.append(ScriptSegment(speaker=speaker, text=text, index=len(segments)))
            continue

        text = _clean_text(stripped)
        if text:
            segments.append(ScriptSegment(speaker=fallback_speaker, text=text, index=len(segments)))

    speakers = _ordered_speakers(segments)
    return ParsedScript(turns=segments, speakers=speakers, speaker_count=len(speakers) or 1)


def _ordered_speakers(segments: list[ScriptSegment]) -> list[str]:
    speakers: list[str] = []
    for segment in segments:
        if segment.is_silence or not segment.speaker:
            continue
        if segment.speaker not in speakers:
            speakers.append(segment.speaker)
    return speakers


def _clean_text(text: str) -> str:
    return _MARKDOWN_STRIP.sub("", text).strip()
