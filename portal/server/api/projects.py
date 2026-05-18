"""项目查看 API — 列表 + 详情"""

import sys
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

_src_path = str(Path(__file__).resolve().parents[4] / "src")
if _src_path not in sys.path:
    sys.path.insert(0, _src_path)

from xy_core.project import Project
from xy_core.exceptions import ProjectNotFound

router = APIRouter()


class ProjectSummary(BaseModel):
    name: str
    client: str
    description: str
    current_state: str
    priority: str
    owner: str
    created_at: str


class ArtifactStatus(BaseModel):
    status: str
    path: str
    produced_by: str = ""


class ReviewStatus(BaseModel):
    status: str
    comments: str = ""
    timestamp: str = ""


class ProjectDetail(BaseModel):
    name: str
    client: str
    description: str
    current_state: str
    priority: str
    owner: str
    deadline: str
    created_at: str
    artifacts: dict[str, ArtifactStatus]
    reviews: dict[str, ReviewStatus]


@router.get("", response_model=list[ProjectSummary])
async def list_projects():
    result = []
    for name in Project.list_projects():
        try:
            p = Project.load(name)
            result.append(ProjectSummary(
                name=name,
                client=p.meta.client,
                description=p.meta.description,
                current_state=p.current_state,
                priority=p.meta.priority,
                owner=p.meta.owner,
                created_at=p.meta.created_at,
            ))
        except Exception:
            continue
    return result


@router.get("/{project_name}", response_model=ProjectDetail)
async def get_project(project_name: str):
    try:
        p = Project.load(project_name)
    except ProjectNotFound:
        raise HTTPException(status_code=404, detail=f"项目 {project_name} 不存在")

    artifacts = {}
    for k, v in p.state.artifacts.items():
        artifacts[k] = ArtifactStatus(**v) if isinstance(v, dict) else ArtifactStatus(status=str(v), path="")

    reviews = {}
    for k, v in p.state.reviews.items():
        reviews[k] = ReviewStatus(**v) if isinstance(v, dict) else ReviewStatus(status=str(v))

    return ProjectDetail(
        name=project_name,
        client=p.meta.client,
        description=p.meta.description,
        current_state=p.current_state,
        priority=p.meta.priority,
        owner=p.meta.owner,
        deadline=p.meta.deadline,
        created_at=p.meta.created_at,
        artifacts=artifacts,
        reviews=reviews,
    )
