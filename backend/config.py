from __future__ import annotations

from config import OPENAI_VOICE_MAP, Provider, base_voice_id


VOICE_CATALOG = [
    # 繁體中文
    {"id": "zh-TW-YunJheNeural", "label": "繁中男聲 1", "provider": Provider.EDGE.value, "language": "zh-TW", "tone": "成人男性"},
    {"id": "zh-TW-YunJheNeural__adult-male-2", "label": "繁中男聲 2", "provider": Provider.EDGE.value, "language": "zh-TW", "tone": "成人男性低沉"},
    {"id": "zh-TW-HsiaoChenNeural", "label": "繁中女聲 1", "provider": Provider.EDGE.value, "language": "zh-TW", "tone": "成人女性"},
    {"id": "zh-TW-HsiaoYuNeural", "label": "繁中女聲 2", "provider": Provider.EDGE.value, "language": "zh-TW", "tone": "成人女性柔和"},
    {"id": "zh-TW-YunJheNeural__boy-1", "label": "繁中小男孩 1", "provider": Provider.EDGE.value, "language": "zh-TW", "tone": "童聲男孩"},
    {"id": "zh-TW-YunJheNeural__boy-2", "label": "繁中小男孩 2", "provider": Provider.EDGE.value, "language": "zh-TW", "tone": "童聲男孩明亮"},
    {"id": "zh-TW-HsiaoChenNeural__girl-1", "label": "繁中小女孩 1", "provider": Provider.EDGE.value, "language": "zh-TW", "tone": "童聲女孩"},
    {"id": "zh-TW-HsiaoYuNeural__girl-2", "label": "繁中小女孩 2", "provider": Provider.EDGE.value, "language": "zh-TW", "tone": "童聲女孩柔和"},
    # English
    {"id": "en-US-AndrewNeural", "label": "English Male 1", "provider": Provider.EDGE.value, "language": "en-US", "tone": "adult male"},
    {"id": "en-US-BrianNeural", "label": "English Male 2", "provider": Provider.EDGE.value, "language": "en-US", "tone": "adult male casual"},
    {"id": "en-US-AvaNeural", "label": "English Female 1", "provider": Provider.EDGE.value, "language": "en-US", "tone": "adult female"},
    {"id": "en-US-EmmaNeural", "label": "English Female 2", "provider": Provider.EDGE.value, "language": "en-US", "tone": "adult female conversational"},
    {"id": "en-US-RogerNeural__boy-1", "label": "English Boy 1", "provider": Provider.EDGE.value, "language": "en-US", "tone": "boy voice"},
    {"id": "en-US-AndrewNeural__boy-2", "label": "English Boy 2", "provider": Provider.EDGE.value, "language": "en-US", "tone": "bright boy voice"},
    {"id": "en-US-AnaNeural", "label": "English Girl 1", "provider": Provider.EDGE.value, "language": "en-US", "tone": "girl voice"},
    {"id": "en-GB-MaisieNeural__girl-2", "label": "English Girl 2", "provider": Provider.EDGE.value, "language": "en-GB", "tone": "bright girl voice"},
    # 日本語
    {"id": "ja-JP-KeitaNeural", "label": "日本語男性 1", "provider": Provider.EDGE.value, "language": "ja-JP", "tone": "成人男性"},
    {"id": "ja-JP-KeitaNeural__adult-male-2", "label": "日本語男性 2", "provider": Provider.EDGE.value, "language": "ja-JP", "tone": "成人男性低め"},
    {"id": "ja-JP-NanamiNeural", "label": "日本語女性 1", "provider": Provider.EDGE.value, "language": "ja-JP", "tone": "成人女性"},
    {"id": "ja-JP-NanamiNeural__adult-female-2", "label": "日本語女性 2", "provider": Provider.EDGE.value, "language": "ja-JP", "tone": "成人女性明るめ"},
    {"id": "ja-JP-KeitaNeural__boy-1", "label": "日本語男の子 1", "provider": Provider.EDGE.value, "language": "ja-JP", "tone": "男の子"},
    {"id": "ja-JP-KeitaNeural__boy-2", "label": "日本語男の子 2", "provider": Provider.EDGE.value, "language": "ja-JP", "tone": "明るい男の子"},
    {"id": "ja-JP-NanamiNeural__girl-1", "label": "日本語女の子 1", "provider": Provider.EDGE.value, "language": "ja-JP", "tone": "女の子"},
    {"id": "ja-JP-NanamiNeural__girl-2", "label": "日本語女の子 2", "provider": Provider.EDGE.value, "language": "ja-JP", "tone": "明るい女の子"},
]


def voice_provider(voice_id: str) -> Provider:
    openai_voices = set(OPENAI_VOICE_MAP.values()) | {"nova", "alloy", "echo", "fable", "onyx", "shimmer"}
    if base_voice_id(voice_id) in openai_voices:
        return Provider.OPENAI
    return Provider.EDGE
