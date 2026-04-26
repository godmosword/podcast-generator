from __future__ import annotations

import re

_SENTENCE_ENDINGS = re.compile(r"(?<=[。！？\n])")


def chunk_text(text: str, max_chars: int = 4096) -> list[str]:
    """Split text into chunks no larger than max_chars, breaking at sentence boundaries."""
    if len(text) <= max_chars:
        return [text]

    sentences = _SENTENCE_ENDINGS.split(text)
    chunks: list[str] = []
    current = ""

    for sentence in sentences:
        if not sentence:
            continue
        if len(current) + len(sentence) > max_chars:
            if current:
                chunks.append(current.strip())
            current = sentence
        else:
            current += sentence

    if current.strip():
        chunks.append(current.strip())

    return chunks or [text]
