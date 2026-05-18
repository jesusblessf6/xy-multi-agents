"""Dashboard API — 聚合视图"""

import sys
from pathlib import Path

from fastapi import APIRouter, Depends
from pydantic import BaseModel

_src_path = str(Path(__file__).resolve().parents[4] / "src")
if _src_path not in sys.path:
    sys.path.insert(0, _src_path)

from xy_core.project import Project
from xy_core.state_machine import StateMachine
from xy_core.review_gate import ReviewGate

from ..dependencies import get_current_user
from ..models.user import User

router = APIRouter()


class DashboardResponse(BaseModel):
    pending_reviews_count: int
    active_projects_count: int
    pending_reviews: list[dict]


@router.get("", response_model=DashboardResponse)
async def get_dashboard(user: User = Depends(get_current_user)):
    """聚合视图：待审数、活跃项目数、待审列表"""
    user_roles = [rb.role for rb in user.roles]
    sm = StateMachine()
    rg = ReviewGate(sm)

    pending = []
    active_count = 0

    for project_name in Project.list_projects():
        try:
            p = Project.load(project_name)
        except Exception:
            continue

        if p.current_state != "delivery":
            active_count += 1

        current = p.current_state
        if sm.is_interrupt_point(current):
            gate_reviewers = sm.get_reviewers(current)
            matched = [r for r in user_roles if r in gate_reviewers]
            if matched or "admin" in user_roles:
                gate_status = rg.get_gate_status(p.dir, current)
                if gate_status != "approved":
                    pending.append({
                        "project_name": project_name,
                        "gate_name": current,
                        "status": gate_status,
                    })

    return DashboardResponse(
        pending_reviews_count=len(pending),
        active_projects_count=active_count,
        pending_reviews=pending,
    )
