from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any


CATALOG_PATH = Path(__file__).parent / "models" / "voice_catalog.json"
VALID_PROVIDERS = {"edge", "openai", "elevenlabs"}
REQUIRED_FIELDS = {"id", "label", "provider", "provider_voice_id", "language", "tone", "tags", "tts_options"}


class VoiceCatalogError(ValueError):
    pass


@lru_cache(maxsize=1)
def _catalog() -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    data = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    voices = data.get("voices")
    if not isinstance(voices, list):
        raise VoiceCatalogError("voice_catalog.json must contain a voices array.")

    normalized: list[dict[str, Any]] = []
    lookup: dict[str, dict[str, Any]] = {}
    for raw in voices:
        if not isinstance(raw, dict):
            raise VoiceCatalogError("Each voice catalog item must be an object.")
        missing = REQUIRED_FIELDS - set(raw)
        if missing:
            raise VoiceCatalogError(f"Voice {raw.get('id', '<unknown>')} is missing fields: {sorted(missing)}")

        item = {
            "id": _string(raw, "id"),
            "label": _string(raw, "label"),
            "provider": _string(raw, "provider"),
            "provider_voice_id": _string(raw, "provider_voice_id"),
            "language": _string(raw, "language"),
            "tone": _string(raw, "tone"),
            "tags": _string_list(raw.get("tags"), "tags"),
            "aliases": _string_list(raw.get("aliases", []), "aliases"),
            "tts_options": _dict(raw.get("tts_options"), "tts_options"),
        }
        if item["provider"] not in VALID_PROVIDERS:
            raise VoiceCatalogError(f"Voice {item['id']} has unsupported provider: {item['provider']}")
        if item["id"] in lookup:
            raise VoiceCatalogError(f"Duplicate voice id: {item['id']}")

        normalized.append(item)
        lookup[item["id"]] = item
        for alias in item["aliases"]:
            if alias in lookup:
                raise VoiceCatalogError(f"Duplicate voice alias: {alias}")
            lookup[alias] = item

    return normalized, lookup


def list_voices() -> list[dict[str, Any]]:
    voices, _ = _catalog()
    return [_public_voice(item) for item in voices]


def get_voice(voice_id: str) -> dict[str, Any] | None:
    _, lookup = _catalog()
    return lookup.get(voice_id)


def is_known_voice(voice_id: str) -> bool:
    return get_voice(voice_id) is not None


def voice_provider(voice_id: str) -> str:
    item = get_voice(voice_id)
    if item:
        return str(item["provider"])
    if voice_id.startswith("elevenlabs:") and len(voice_id) > len("elevenlabs:"):
        return "elevenlabs"
    return "edge"


def provider_voice_id(voice_id: str) -> str:
    item = get_voice(voice_id)
    if item:
        return str(item["provider_voice_id"])
    return voice_id.removeprefix("elevenlabs:")


def tts_options_for(voice_id: str) -> dict[str, Any]:
    item = get_voice(voice_id)
    if not item:
        return {}
    return dict(item["tts_options"])


def canonical_voice_id(voice_id: str) -> str:
    item = get_voice(voice_id)
    if not item:
        return voice_id
    return str(item["id"])


def _public_voice(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": item["id"],
        "label": item["label"],
        "provider": item["provider"],
        "provider_voice_id": item["provider_voice_id"],
        "language": item["language"],
        "tone": item["tone"],
        "tags": list(item["tags"]),
        "source": "static",
    }


def _string(raw: dict[str, Any], key: str) -> str:
    value = raw.get(key)
    if not isinstance(value, str) or not value.strip():
        raise VoiceCatalogError(f"Voice field {key} must be a non-empty string.")
    return value.strip()


def _string_list(value: Any, key: str) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) and item.strip() for item in value):
        raise VoiceCatalogError(f"Voice field {key} must be a list of non-empty strings.")
    return [item.strip() for item in value]


def _dict(value: Any, key: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise VoiceCatalogError(f"Voice field {key} must be an object.")
    return dict(value)
