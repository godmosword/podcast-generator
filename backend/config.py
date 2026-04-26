from __future__ import annotations

from config import OPENAI_VOICE_MAP, Provider, base_voice_id


VOICE_CATALOG = [
    # 繁體中文
    {"id": "zh-TW-YunJheNeural", "label": "建宏", "provider": Provider.EDGE.value, "language": "zh-TW", "tone": "成人男聲"},
    {"id": "zh-TW-YunJheNeural__adult-male-2", "label": "柏宇", "provider": Provider.EDGE.value, "language": "zh-TW", "tone": "成人男聲低沉"},
    {"id": "zh-TW-HsiaoChenNeural", "label": "雅琪", "provider": Provider.EDGE.value, "language": "zh-TW", "tone": "成人女聲"},
    {"id": "zh-TW-HsiaoYuNeural", "label": "靜怡", "provider": Provider.EDGE.value, "language": "zh-TW", "tone": "成人女聲柔和"},
    {"id": "zh-TW-YunJheNeural__boy-1", "label": "小宇", "provider": Provider.EDGE.value, "language": "zh-TW", "tone": "5歲小男孩"},
    {"id": "zh-TW-YunJheNeural__boy-2", "label": "小傑", "provider": Provider.EDGE.value, "language": "zh-TW", "tone": "5歲小男孩明亮"},
    {"id": "zh-TW-HsiaoChenNeural__girl-1", "label": "小安", "provider": Provider.EDGE.value, "language": "zh-TW", "tone": "5歲小女孩"},
    {"id": "zh-TW-HsiaoYuNeural__girl-2", "label": "小晴", "provider": Provider.EDGE.value, "language": "zh-TW", "tone": "5歲小女孩柔和"},
    # English
    {"id": "en-US-AndrewNeural", "label": "Andrew", "provider": Provider.EDGE.value, "language": "en-US", "tone": "adult male"},
    {"id": "en-US-BrianNeural", "label": "Brian", "provider": Provider.EDGE.value, "language": "en-US", "tone": "adult male casual"},
    {"id": "en-US-AvaNeural", "label": "Ava", "provider": Provider.EDGE.value, "language": "en-US", "tone": "adult female"},
    {"id": "en-US-EmmaNeural", "label": "Emma", "provider": Provider.EDGE.value, "language": "en-US", "tone": "adult female conversational"},
    {"id": "en-US-RogerNeural__boy-1", "label": "Oliver", "provider": Provider.EDGE.value, "language": "en-US", "tone": "5-year-old boy"},
    {"id": "en-US-AndrewNeural__boy-2", "label": "Leo", "provider": Provider.EDGE.value, "language": "en-US", "tone": "bright 5-year-old boy"},
    {"id": "en-US-AnaNeural", "label": "Ana", "provider": Provider.EDGE.value, "language": "en-US", "tone": "5-year-old girl"},
    {"id": "en-GB-MaisieNeural__girl-2", "label": "Maisie", "provider": Provider.EDGE.value, "language": "en-GB", "tone": "bright 5-year-old girl"},
    # 日本語
    {"id": "ja-JP-KeitaNeural", "label": "啓太", "provider": Provider.EDGE.value, "language": "ja-JP", "tone": "成人男性"},
    {"id": "ja-JP-KeitaNeural__adult-male-2", "label": "悠真", "provider": Provider.EDGE.value, "language": "ja-JP", "tone": "成人男性低め"},
    {"id": "ja-JP-NanamiNeural", "label": "七海", "provider": Provider.EDGE.value, "language": "ja-JP", "tone": "成人女性"},
    {"id": "ja-JP-NanamiNeural__adult-female-2", "label": "葵", "provider": Provider.EDGE.value, "language": "ja-JP", "tone": "成人女性明るめ"},
    {"id": "ja-JP-KeitaNeural__boy-1", "label": "湊", "provider": Provider.EDGE.value, "language": "ja-JP", "tone": "5歳男の子"},
    {"id": "ja-JP-KeitaNeural__boy-2", "label": "陽翔", "provider": Provider.EDGE.value, "language": "ja-JP", "tone": "明るい5歳男の子"},
    {"id": "ja-JP-NanamiNeural__girl-1", "label": "結菜", "provider": Provider.EDGE.value, "language": "ja-JP", "tone": "5歳女の子"},
    {"id": "ja-JP-NanamiNeural__girl-2", "label": "陽菜", "provider": Provider.EDGE.value, "language": "ja-JP", "tone": "明るい5歳女の子"},
]


def voice_provider(voice_id: str) -> Provider:
    openai_voices = set(OPENAI_VOICE_MAP.values()) | {"nova", "alloy", "echo", "fable", "onyx", "shimmer"}
    if base_voice_id(voice_id) in openai_voices:
        return Provider.OPENAI
    return Provider.EDGE
