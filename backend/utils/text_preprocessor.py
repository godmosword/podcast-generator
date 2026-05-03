from __future__ import annotations

from opencc import OpenCC

# Traditional → Simplified; improves naturalness for OpenAI TTS and Edge TTS
# (zh-TW Edge voices still accept simplified input and produce cleaner output)
_t2s = OpenCC("t2s")


def preprocess_for_tts(text: str) -> str:
    """Normalise text before TTS synthesis.

    Converts Traditional Chinese to Simplified and strips characters that
    TTS engines tend to misread or skip.
    """
    if not text:
        return text
    text = _t2s.convert(text)
    # Replace full-width colon with ASCII so TTS reads it as a pause, not a word
    text = text.replace("…", "...")  # … → ...
    return text.strip()
