from __future__ import annotations

from config import DEFAULT_VOICE_MAP, OPENAI_VOICE_MAP, Provider


VOICE_CATALOG = [
    {
        "id": "zh-TW-HsiaoChenNeural",
        "label": "雅琪",
        "provider": Provider.EDGE.value,
        "language": "zh-TW",
        "tone": "清亮穩定",
    },
    {
        "id": "zh-TW-YunJheNeural",
        "label": "建宏",
        "provider": Provider.EDGE.value,
        "language": "zh-TW",
        "tone": "溫和低頻",
    },
    {
        "id": "zh-TW-HsiaoYuNeural",
        "label": "靜怡",
        "provider": Provider.EDGE.value,
        "language": "zh-TW",
        "tone": "親切柔和",
    },
    {
        "id": "zh-CN-YunxiNeural",
        "label": "雲希",
        "provider": Provider.EDGE.value,
        "language": "zh-CN",
        "tone": "年輕清晰",
    },
    {
        "id": "alloy",
        "label": "Alloy",
        "provider": Provider.OPENAI.value,
        "language": "multilingual",
        "tone": "自然中性",
    },
]


def voice_provider(voice_id: str) -> Provider:
    edge_voices = set(DEFAULT_VOICE_MAP.values()) | {"zh-TW-HsiaoYuNeural", "zh-CN-YunxiNeural"}
    openai_voices = set(OPENAI_VOICE_MAP.values()) | {"nova", "alloy"}
    if voice_id in openai_voices and voice_id not in edge_voices:
        return Provider.OPENAI
    return Provider.EDGE
