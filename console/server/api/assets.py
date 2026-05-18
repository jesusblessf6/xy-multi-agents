"""资产管理 API — Skills/RAG/Plugins CRUD"""

import sys
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

# 注入 src/ 到 sys.path 以便 import xy_core
_src_path = str(Path(__file__).resolve().parents[4] / "src")
if _src_path not in sys.path:
    sys.path.insert(0, _src_path)

from xy_core.agent_registry import (
    list_agents as _list_agents,
    load_agent_config,
    get_skills, get_skill, get_skill_summaries,
    save_skill, delete_skill, validate_skill_frontmatter,
    get_rag_docs, get_rag_content, save_rag_doc, delete_rag_doc,
)

from ..dependencies import can_operate_agent, get_current_user
from ..models.user import User

router = APIRouter()


class SkillInfo(BaseModel):
    name: str
    description: str
    allowed_tools: list[str]
    file_path: str = ""


class SkillContent(BaseModel):
    name: str
    description: str
    allowed_tools: list[str]
    content: str


class SkillSaveRequest(BaseModel):
    content: str


class AgentInfo(BaseModel):
    name: str
    display_name: str
    can_edit: bool
    skills_count: int
    rag_count: int


class RagDocInfo(BaseModel):
    name: str
    file_path: str


class RagContentResponse(BaseModel):
    name: str
    content: str


def _check_agent_access(user: User, agent_name: str):
    if not can_operate_agent(user, agent_name):
        raise HTTPException(status_code=403, detail=f"无权操作 {agent_name} Agent")


# ── Agent 列表 ────────────────────────────────


@router.get("", response_model=list[AgentInfo])
async def list_agents_view(user: User = Depends(get_current_user)):
    agents = _list_agents()
    result = []
    for name in agents:
        config = load_agent_config(name)
        skills = get_skill_summaries(name)
        rags = get_rag_docs(name)
        result.append(AgentInfo(
            name=name,
            display_name=config.display_name,
            can_edit=can_operate_agent(user, name),
            skills_count=len(skills),
            rag_count=len(rags),
        ))
    return result


@router.get("/{agent_name}", response_model=AgentInfo)
async def get_agent_detail(
    agent_name: str,
    user: User = Depends(get_current_user),
):
    config = load_agent_config(agent_name)
    skills = get_skill_summaries(agent_name)
    rags = get_rag_docs(agent_name)
    return AgentInfo(
        name=agent_name,
        display_name=config.display_name,
        can_edit=can_operate_agent(user, agent_name),
        skills_count=len(skills),
        rag_count=len(rags),
    )


# ── Skills ────────────────────────────────────


@router.get("/{agent_name}/skills", response_model=list[SkillInfo])
async def list_skills(
    agent_name: str,
    user: User = Depends(get_current_user),
):
    return get_skill_summaries(agent_name)


@router.get("/{agent_name}/skills/{skill_name}", response_model=SkillContent)
async def read_skill(
    agent_name: str,
    skill_name: str,
    user: User = Depends(get_current_user),
):
    skill = get_skill(agent_name, skill_name)
    return SkillContent(**skill.model_dump())


@router.put("/{agent_name}/skills/{skill_name}")
async def write_skill(
    agent_name: str,
    skill_name: str,
    req: SkillSaveRequest,
    user: User = Depends(get_current_user),
):
    _check_agent_access(user, agent_name)
    valid, error = validate_skill_frontmatter(req.content)
    if not valid:
        raise HTTPException(status_code=400, detail=f"SKILL.md 格式错误: {error}")
    path = save_skill(agent_name, skill_name, req.content)
    return {"saved": str(path)}


@router.delete("/{agent_name}/skills/{skill_name}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_skill(
    agent_name: str,
    skill_name: str,
    user: User = Depends(get_current_user),
):
    _check_agent_access(user, agent_name)
    delete_skill(agent_name, skill_name)


# ── RAG ───────────────────────────────────────


@router.get("/{agent_name}/rag", response_model=list[RagDocInfo])
async def list_rag(
    agent_name: str,
    user: User = Depends(get_current_user),
):
    return get_rag_docs(agent_name)


@router.get("/{agent_name}/rag/{doc_name}", response_model=RagContentResponse)
async def read_rag(
    agent_name: str,
    doc_name: str,
    user: User = Depends(get_current_user),
):
    content = get_rag_content(agent_name, doc_name)
    return RagContentResponse(name=doc_name, content=content)


@router.put("/{agent_name}/rag/{doc_name}")
async def write_rag(
    agent_name: str,
    doc_name: str,
    req: SkillSaveRequest,
    user: User = Depends(get_current_user),
):
    _check_agent_access(user, agent_name)
    path = save_rag_doc(agent_name, doc_name, req.content)
    return {"saved": str(path)}


@router.delete("/{agent_name}/rag/{doc_name}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_rag(
    agent_name: str,
    doc_name: str,
    user: User = Depends(get_current_user),
):
    _check_agent_access(user, agent_name)
    delete_rag_doc(agent_name, doc_name)
