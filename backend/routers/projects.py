from __future__ import annotations

from fastapi import APIRouter, HTTPException

from backend.models.schemas import ProjectCreate, ProjectResponse, ProjectSummary, ProjectUpdate
from backend.projects import create_project, get_project, list_projects, update_project

router = APIRouter(prefix="/api/projects", tags=["projects"])


@router.post("", response_model=ProjectResponse, status_code=201)
async def create_new_project(payload: ProjectCreate) -> ProjectResponse:
    return ProjectResponse(**create_project(**payload.model_dump()))


@router.get("", response_model=list[ProjectSummary])
async def get_project_list() -> list[ProjectSummary]:
    return [ProjectSummary(**p) for p in list_projects()]


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_single_project(project_id: str) -> ProjectResponse:
    project = get_project(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found.")
    return ProjectResponse(**project)


@router.patch("/{project_id}", response_model=ProjectResponse)
async def patch_project(project_id: str, payload: ProjectUpdate) -> ProjectResponse:
    updates = {k: v for k, v in payload.model_dump().items() if v is not None}
    project = update_project(project_id, **updates)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found.")
    return ProjectResponse(**project)
