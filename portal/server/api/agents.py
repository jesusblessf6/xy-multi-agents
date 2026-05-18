"""Agent 列表 API"""

import sys
from pathlib import Path

from fastapi import APIRouter
from pydantic import BaseModel

_src_path = str(Path(__file__).resolve().parents[4] / "src")
if _src_path not in sys.path:
    sys.path.insert(0, _src_path)

from xy_core.agent_registry import list_agents, load_agent_config, get_skill_summaries, get_rag_docs

router = APIRouter()


class AgentInfo(BaseModel):
    name: str
    display_name: str
    role: str
    output_dir: str
    skills_count: int
    rag_count: int
    is_orchestrator: bool


@router.get("", response_model=list[AgentInfo])
async def list_agents_view():
    result = []
    for name in list_agents():
        config = load_agent_config(name)
        skills = get_skill_summaries(name)
        rags = get_rag_docs(name)
        result.append(AgentInfo(
            name=name,
            display_name=config.display_name,
            role=config.role[:80],
            output_dir=config.output_dir,
            skills_count=len(skills),
            rag_count=len(rags),
            is_orchestrator=config.is_orchestrator,
        ))
    return result
