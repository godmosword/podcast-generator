from __future__ import annotations

import re
from dataclasses import dataclass, field

import anthropic

from utils.script_metrics import measure_script, target_units_for_duration


@dataclass(frozen=True)
class ScriptSpec:
    topic: str
    duration_min: int
    host_count: int
    tone: str
    language: str
    extra_context: str | None = None


@dataclass
class ScriptDraft:
    script: str
    estimated_duration_sec: int
    warnings: list[str] = field(default_factory=list)


_TONE_LABELS: dict[str, str] = {
    "educational": "educationally, explaining concepts clearly with examples",
    "entertainment": "entertainingly with humor, energy, and engaging banter",
    "storytelling": "as a narrative story with vivid descriptions",
    "interview": "as an interview — one host asks questions, guest(s) respond in depth",
    "debate": "as a debate exploring multiple perspectives on the topic",
}

_LANG_LABELS: dict[str, str] = {
    "zh-TW": "Traditional Chinese (繁體中文)",
    "zh-CN": "Simplified Chinese (简体中文)",
    "en": "English",
    "ja": "Japanese",
}


def _build_system_prompt(spec: ScriptSpec) -> str:
    host_list = "、".join(f"主持人{chr(64 + i)}" for i in range(1, spec.host_count + 1))
    target_units, unit_label, _, _ = target_units_for_duration(spec.duration_min, spec.language)
    lang_label = _LANG_LABELS.get(spec.language, spec.language)
    tone_label = _TONE_LABELS.get(spec.tone, spec.tone)
    conversational_note = (
        "9. Include natural interjections (嗯、對啊、有意思、哇、真的嗎) to make dialogue feel real"
        if spec.tone in {"entertainment", "interview", "debate"}
        else ""
    )

    return f"""You are a professional podcast script writer. Write a {spec.duration_min}-minute podcast in {lang_label}.

STRICT OUTPUT FORMAT — every line must look exactly like this:
[主持人A]: dialogue text here
[主持人B]: dialogue text here

RULES:
1. Use ONLY these speaker tags: {host_list}
2. NO narration, stage directions, markdown headings, or explanatory text outside of speaker lines
3. Each turn: 1–4 sentences, vary length naturally for rhythm
4. Target exactly {target_units} {unit_label} total (±15%), excluding speaker tags
5. Style: {tone_label}
6. Distribute speaking time evenly across all {spec.host_count} host(s)
7. Begin with a natural opening — host greetings, brief topic intro
8. Insert a natural topic transition every 3 minutes of content{f'{chr(10)}{conversational_note}' if conversational_note else ''}

Start immediately with the first speaker line. Output nothing else."""


def _validate_and_clean(raw: str, spec: ScriptSpec) -> tuple[str, list[str]]:
    warnings: list[str] = []
    valid_speakers = {f"主持人{chr(64 + i)}" for i in range(1, spec.host_count + 1)}
    if spec.host_count == 1:
        valid_speakers.add("主持人")

    clean_lines: list[str] = []
    for line in raw.strip().splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        match = re.match(r"^\[(.+?)\][:：]\s*(.+)$", stripped)
        if match:
            speaker, text = match.group(1), match.group(2)
            if speaker in valid_speakers:
                clean_lines.append(f"[{speaker}]: {text}")
            else:
                warnings.append(f"Unknown speaker '{speaker}' was removed.")

    script = "\n".join(clean_lines)
    metrics = measure_script(script, spec.language)
    target, _, short_label, _ = target_units_for_duration(spec.duration_min, spec.language)
    ratio = metrics.unit_count / max(1, target)
    if ratio < 0.70:
        warnings.append(f"Script may be too short ({metrics.unit_count} {short_label}, target ~{target}).")
    elif ratio > 1.35:
        warnings.append(f"Script may be too long ({metrics.unit_count} {short_label}, target ~{target}).")

    return script, warnings


async def generate_script(spec: ScriptSpec, api_key: str) -> ScriptDraft:
    client = anthropic.AsyncAnthropic(api_key=api_key)
    system_prompt = _build_system_prompt(spec)

    user_content = f"Topic: {spec.topic}"
    if spec.extra_context:
        user_content += f"\n\nAdditional context: {spec.extra_context}"

    message = await client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=8192,
        system=system_prompt,
        messages=[{"role": "user", "content": user_content}],
    )

    raw = message.content[0].text if message.content else ""
    script, warnings = _validate_and_clean(raw, spec)

    # Single retry when too short
    metrics = measure_script(script, spec.language)
    target, _, short_label, per_minute = target_units_for_duration(spec.duration_min, spec.language)
    if metrics.unit_count < int(spec.duration_min * per_minute * 0.70):
        retry = await client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=8192,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_content},
                {"role": "assistant", "content": raw},
                {
                    "role": "user",
                    "content": (
                        f"The script is too short ({metrics.unit_count} {short_label}). "
                        f"Continue the dialogue to reach ~{target} {short_label} total. "
                        "Same format, pick up naturally from the last line."
                    ),
                },
            ],
        )
        extra_raw = retry.content[0].text if retry.content else ""
        script, warnings = _validate_and_clean(raw + "\n" + extra_raw, spec)
        metrics = measure_script(script, spec.language)

    return ScriptDraft(script=script, estimated_duration_sec=metrics.estimated_duration_sec, warnings=warnings)
