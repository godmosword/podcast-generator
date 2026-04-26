from __future__ import annotations

from config import DEFAULT_VOICE_MAP, OPENAI_VOICE_MAP, Provider


VOICE_CATALOG = [
    # 繁體中文
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
    # 簡體中文
    {
        "id": "zh-CN-YunxiNeural",
        "label": "雲希",
        "provider": Provider.EDGE.value,
        "language": "zh-CN",
        "tone": "年輕清晰",
    },
    {
        "id": "zh-CN-XiaoxiaoNeural",
        "label": "曉曉",
        "provider": Provider.EDGE.value,
        "language": "zh-CN",
        "tone": "溫暖親切",
    },
    # 英語
    {
        "id": "en-US-JennyNeural",
        "label": "Jenny",
        "provider": Provider.EDGE.value,
        "language": "en-US",
        "tone": "friendly",
    },
    {
        "id": "en-US-GuyNeural",
        "label": "Guy",
        "provider": Provider.EDGE.value,
        "language": "en-US",
        "tone": "casual",
    },
    {
        "id": "en-GB-SoniaNeural",
        "label": "Sonia",
        "provider": Provider.EDGE.value,
        "language": "en-GB",
        "tone": "formal",
    },
    # 日語
    {
        "id": "ja-JP-NanamiNeural",
        "label": "Nanami",
        "provider": Provider.EDGE.value,
        "language": "ja-JP",
        "tone": "gentle",
    },
    {
        "id": "ja-JP-KeitaNeural",
        "label": "Keita",
        "provider": Provider.EDGE.value,
        "language": "ja-JP",
        "tone": "natural",
    },
    # 韓語
    {
        "id": "ko-KR-SunHiNeural",
        "label": "SunHi",
        "provider": Provider.EDGE.value,
        "language": "ko-KR",
        "tone": "bright",
    },
    {
        "id": "ko-KR-InJoonNeural",
        "label": "InJoon",
        "provider": Provider.EDGE.value,
        "language": "ko-KR",
        "tone": "calm",
    },
    # 法語
    {
        "id": "fr-FR-DeniseNeural",
        "label": "Denise",
        "provider": Provider.EDGE.value,
        "language": "fr-FR",
        "tone": "expressive",
    },
    # 西班牙語
    {
        "id": "es-ES-ElviraNeural",
        "label": "Elvira",
        "provider": Provider.EDGE.value,
        "language": "es-ES",
        "tone": "vivid",
    },
    # OpenAI
    {
        "id": "alloy",
        "label": "Alloy",
        "provider": Provider.OPENAI.value,
        "language": "multilingual",
        "tone": "自然中性",
    },
]


def voice_provider(voice_id: str) -> Provider:
    openai_voices = set(OPENAI_VOICE_MAP.values()) | {"nova", "alloy", "echo", "fable", "onyx", "shimmer"}
    # Edge TTS voices follow the BCP-47 format: xx-XX-NameNeural
    if voice_id in openai_voices:
        return Provider.OPENAI
    return Provider.EDGE
