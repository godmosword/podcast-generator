from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import VOICE_CATALOG
from backend.routers import analyze, bgm, classics, files, generate, preview, script
from config import Config

app = FastAPI(title="Wavescript API", version="0.1.0")
config = Config()

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.cors_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(generate.router)
app.include_router(preview.router)
app.include_router(files.router)
app.include_router(bgm.router)
app.include_router(classics.router)
app.include_router(script.router)
app.include_router(analyze.router)


@app.get("/api/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/voices")
async def voices() -> list[dict[str, str]]:
    return VOICE_CATALOG + await _elevenlabs_voice_catalog()


async def _elevenlabs_voice_catalog() -> list[dict[str, str]]:
    if not config.elevenlabs_api_key:
        return []
    try:
        from elevenlabs.client import AsyncElevenLabs

        client = AsyncElevenLabs(api_key=config.elevenlabs_api_key)
        response = await client.voices.get_all()
    except Exception:
        return []

    items: list[dict[str, str]] = []
    for voice in getattr(response, "voices", []) or []:
        voice_id = getattr(voice, "voice_id", "")
        name = getattr(voice, "name", voice_id)
        if not voice_id:
            continue
        labels = getattr(voice, "labels", None) or {}
        language = str(labels.get("language") or labels.get("accent") or "multi")
        tone = str(labels.get("description") or labels.get("gender") or getattr(voice, "category", "") or "custom voice")
        items.append(
            {
                "id": f"elevenlabs:{voice_id}",
                "label": str(name),
                "provider": "elevenlabs",
                "language": language,
                "tone": tone,
            }
        )
    static_ids = {item["id"] for item in VOICE_CATALOG}
    return [item for item in items if item["id"] not in static_ids]
