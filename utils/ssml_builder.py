from __future__ import annotations

import re

_PAUSE_MAP = {
    "，": 200,
    ",": 150,
    "。": 400,
    ".": 300,
    "！": 350,
    "!": 300,
    "？": 350,
    "?": 300,
    "；": 250,
    ";": 200,
}

PAUSE_MAP = _PAUSE_MAP  # public alias


def build_ssml(text: str, rate: str = "medium", pitch: str = "medium") -> str:
    """Build SSML markup with natural break points at punctuation."""
    escaped = (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )

    def insert_break(m: re.Match) -> str:
        char = m.group(0)
        ms = _PAUSE_MAP.get(char, 200)
        return f'{char}<break time="{ms}ms"/>'

    pattern = re.compile(r"[，,。.！!？?；;]")
    body = pattern.sub(insert_break, escaped)

    return (
        f'<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="zh-TW">'
        f'<prosody rate="{rate}" pitch="{pitch}">{body}</prosody>'
        f"</speak>"
    )


def strip_ssml(ssml: str) -> str:
    """Remove SSML tags, returning plain text."""
    return re.sub(r"<[^>]+>", "", ssml)
