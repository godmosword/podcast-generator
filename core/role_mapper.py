from __future__ import annotations

from config import Config


class RoleMappingError(ValueError):
    pass


def map_roles_to_voices(
    speakers: list[str],
    config: Config,
    overrides: dict[str, str] | None = None,
    max_speakers: int = 4,
) -> dict[str, str]:
    """Map parsed speaker names to provider voice ids.

    Overrides from the UI win first. Remaining speakers are assigned from the
    provider's configured voice map, then rotate through the available defaults.
    """
    if len(speakers) > max_speakers:
        raise RoleMappingError(f"Only 1-{max_speakers} speakers are supported; found {len(speakers)}.")

    if not speakers:
        speakers = ["speaker_1"]

    mapping = config.voice_map()
    voice_pool = [voice for key, voice in mapping.items() if key != "_default"] or [mapping["_default"]]
    overrides = overrides or {}
    result: dict[str, str] = {}

    for index, speaker in enumerate(speakers):
        result[speaker] = overrides.get(speaker) or mapping.get(speaker) or voice_pool[index % len(voice_pool)]

    return result
