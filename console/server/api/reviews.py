"""评审 API — 待审列表 + 提交审批决定"""

import sys
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

_src_path = str(Path(__file__).resolve().parents[4] / "src")
if _src_path not in sys.path:
    sys.path.insert(0, _src_path)

from xy_core.project import Project
from xy_core.review_gate import ReviewGate
from xy_core.state_machine import StateMachine

from ..dependencies import get_current_user
from ..models.user import User

router = APIRouter()


class ReviewSubmitRequest(BaseModel):
    approved: bool
    comments: str = ""


class ReviewPendingItem(BaseModel):
    project_name: str
    gate_name: str
    status: str
    reviewers_required: list[str]
    decided_reviewers: list[str]


class ReviewDetail(BaseModel):
    project_name: str
    gate_name: str
    status: str
    reviewers_required: list[str]
    decisions: list[dict]
    checklist: list[str]


@router.get("/pending", response_model=list[ReviewPendingItem])
async def list_pending_reviews(user: User = Depends(get_current_user)):
    """列出当前用户有权审批的待审项目"""
    user_roles = [rb.role for rb in user.roles]
    sm = StateMachine()
    rg = ReviewGate(sm)
    result = []

    for project_name in Project.list_projects():
        try:
            p = Project.load(project_name)
        except Exception:
            continue

        current = p.current_state
        if not sm.is_interrupt_point(current):
            continue

        # 检查用户角色是否匹配该评审门
        gate_reviewers = sm.get_reviewers(current)
        matched_roles = [r for r in user_roles if r in gate_reviewers]
        if not matched_roles and "admin" not in user_roles:
            continue

        gate_status = rg.get_gate_status(p.dir, current)
        if gate_status == "approved":
            continue

        # 获取已决定的审核人
        decided = []
        if gate_status != "not_created":
            try:
                record = rg.load_record(p.dir, current)
                decided = [d.reviewer_role for d in record.decisions]
            except Exception:
                pass

        result.append(ReviewPendingItem(
            project_name=project_name,
            gate_name=current,
            status=gate_status,
            reviewers_required=gate_reviewers,
            decided_reviewers=decided,
        ))

    return result


@router.get("/{project_name}/{gate_name}", response_model=ReviewDetail)
async def get_review_detail(
    project_name: str,
    gate_name: str,
    user: User = Depends(get_current_user),
):
    """获取评审详情（含产出物预览）"""
    try:
        p = Project.load(project_name)
    except Exception:
        raise HTTPException(status_code=404, detail="项目不存在")

    sm = StateMachine()
    rg = ReviewGate(sm)

    try:
        record = rg.load_record(p.dir, gate_name)
    except Exception:
        raise HTTPException(status_code=404, detail="评审记录不存在")

    # 获取检查清单
    checklist = []
    pipeline = sm.pipeline
    if gate_name in pipeline.review_gates:
        checklist = pipeline.review_gates[gate_name].checklist

    return ReviewDetail(
        project_name=project_name,
        gate_name=gate_name,
        status=record.status,
        reviewers_required=record.reviewers_required,
        decisions=[d.model_dump() for d in record.decisions],
        checklist=checklist,
    )


@router.post("/{project_name}/{gate_name}")
async def submit_review(
    project_name: str,
    gate_name: str,
    req: ReviewSubmitRequest,
    user: User = Depends(get_current_user),
):
    """提交审批决定"""
    user_roles = [rb.role for rb in user.roles]
    sm = StateMachine()
    rg = ReviewGate(sm)

    # 自动匹配审核人角色
    gate_reviewers = sm.get_reviewers(gate_name)
    matched_roles = [r for r in user_roles if r in gate_reviewers]
    if not matched_roles and "admin" not in user_roles:
        raise HTTPException(status_code=403, detail="无权参与此评审")

    try:
        p = Project.load(project_name)
    except Exception:
        raise HTTPException(status_code=404, detail="项目不存在")

    # 用第一个匹配的角色提交（admin用第一个reviewer角色）
    reviewer_role = matched_roles[0] if matched_roles else gate_reviewers[0]

    try:
        record = rg.submit_decision(
            p.dir, gate_name,
            reviewer_role=reviewer_role,
            approved=req.approved,
            comments=req.comments,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    # 评审结束后自动流转状态
    if record.status == "approved":
        next_state = sm.get_next_state(gate_name, "review_approved")
        if next_state:
            p.transition_to(next_state)
    elif record.status == "rejected":
        next_state = sm.get_next_state(gate_name, "review_rejected")
        if next_state:
            p.transition_to(next_state)

    return {
        "gate_name": gate_name,
        "status": record.status,
        "reviewer": reviewer_role,
    }
