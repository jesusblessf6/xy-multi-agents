"""需求提交 API"""

import sys
from pathlib import Path

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

_src_path = str(Path(__file__).resolve().parents[4] / "src")
if _src_path not in sys.path:
    sys.path.insert(0, _src_path)

from xy_core.project import Project
from xy_core.exceptions import ProjectAlreadyExists

router = APIRouter()


class SubmitRequirementRequest(BaseModel):
    project_name: str
    client: str = ""
    description: str = ""
    requirement_text: str
    owner: str = ""
    priority: str = "normal"


class SubmitRequirementResponse(BaseModel):
    project_name: str
    status: str
    message: str


@router.post("", response_model=SubmitRequirementResponse, status_code=status.HTTP_201_CREATED)
async def submit_requirement(req: SubmitRequirementRequest):
    """提交需求，创建项目并直接进入 requirements 状态"""
    try:
        p = Project.create_with_requirement(
            name=req.project_name,
            requirement_text=req.requirement_text,
            client=req.client,
            description=req.description,
            owner=req.owner,
            priority=req.priority,
        )
        return SubmitRequirementResponse(
            project_name=req.project_name,
            status="idle",
            message=f"项目已创建，原始需求已写入 {p.dir}/00_raw_input/raw_requirement.md，等待售前Agent处理",
        )
    except ProjectAlreadyExists:
        raise HTTPException(status_code=400, detail=f"项目 {req.project_name} 已存在")
