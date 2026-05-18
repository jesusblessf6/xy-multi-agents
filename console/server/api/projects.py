"""项目查看 API — 项目列表 + 详情 + 产出物内容"""

import sys
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

_src_path = str(Path(__file__).resolve().parents[4] / "src")
if _src_path not in sys.path:
    sys.path.insert(0, _src_path)

from xy_core.project import Project
from xy_core.state_machine import StateMachine

from ..dependencies import get_current_user
from ..models.user import User

router = APIRouter()


class ProjectSummary(BaseModel):
    name: str
    client: str
    current_state: str
    created_at: str


class ProjectDetail(BaseModel):
    name: str
    client: str
    description: str
    current_state: str
    created_at: str
    artifacts: dict
    reviews: dict


@router.get("", response_model=list[ProjectSummary])
async def list_projects(user: User = Depends(get_current_user)):
    result = []
    for name in Project.list_projects():
        try:
            p = Project.load(name)
            result.append(ProjectSummary(
                name=name,
                client=p.meta.client,
                current_state=p.current_state,
                created_at=p.meta.created_at,
            ))
        except Exception:
            continue
    return result


@router.get("/{project_name}", response_model=ProjectDetail)
async def get_project(
    project_name: str,
    user: User = Depends(get_current_user),
):
    try:
        p = Project.load(project_name)
    except Exception:
        raise HTTPException(status_code=404, detail="项目不存在")

    return ProjectDetail(
        name=project_name,
        client=p.meta.client,
        description=p.meta.description,
        current_state=p.current_state,
        created_at=p.meta.created_at,
        artifacts={k: v.model_dump() if hasattr(v, "model_dump") else v
                   for k, v in p.state.artifacts.items()},
        reviews={k: v.model_dump() if hasattr(v, "model_dump") else v
                 for k, v in p.state.reviews.items()},
    )


@router.get("/{project_name}/artifacts/{artifact_name}")
async def get_artifact_content(
    project_name: str,
    artifact_name: str,
    user: User = Depends(get_current_user),
):
    try:
        p = Project.load(project_name)
        content = p.get_artifact_content(artifact_name)
        return {"name": artifact_name, "content": content}
    except KeyError:
        raise HTTPException(status_code=404, detail=f"未知产出物: {artifact_name}")
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))
