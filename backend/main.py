from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import VOICE_CATALOG
from backend.routers import bgm, files, generate, preview

app = FastAPI(title="Wavescript API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(generate.router)
app.include_router(preview.router)
app.include_router(files.router)
app.include_router(bgm.router)


@app.get("/api/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/voices")
async def voices() -> list[dict[str, str]]:
    return VOICE_CATALOG
