from __future__ import annotations

from typing import Any, Literal

from fastapi import APIRouter, HTTPException, Query

from backend.classics_catalog import ClassicNotFoundError, get_classic_script, list_classics

router = APIRouter(prefix="/api", tags=["classics"])


@router.get("/classics")
async def classics_catalog(
    duration_category: Literal["short", "medium", "long"] | None = Query(default=None),
) -> list[dict[str, Any]]:
    return [c.to_public_dict() for c in list_classics(duration_category=duration_category)]


@router.get("/classics/{classic_id}/script")
async def classic_script(classic_id: str) -> dict[str, str]:
    try:
        text = get_classic_script(classic_id)
    except ClassicNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"id": classic_id, "script": text}
