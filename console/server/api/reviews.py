"""评审 API — 待审列表 + 提交审批决定 + Agent评审触发"""

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

from ..dependencies import get_current_user, require_admin
from ..models.user import User

router = APIRouter()


class ReviewSubmitRequest(BaseModel):
    approved: bool
    comments: str = ""


class ReviewPendingItem(BaseModel):
    project_name: str
    gate_name: str
    gate_type: str  # "human_audit" | "agent_review"
    status: str
    reviewers_required: list[str]
    decided_reviewers: list[str]


class ReviewDetail(BaseModel):
    project_name: str
    gate_name: str
    gate_type: str
    status: str
    reviewers_required: list[str]
    decisions: list[dict]
    checklist: list[str] = []
    review_input: str | None = None


@router.get("/pending", response_model=list[ReviewPendingItem])
async def list_pending_reviews(user: User = Depends(get_current_user)):
    """列出当前用户有权审批的待审项目

    - human_audit 门：阻塞等待人工操作，显示在待审列表
    - agent_review 门：系统自动派发，仅显示状态
    """
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
            # 不是人审门，检查是否为 agent_review 门
            if sm.is_agent_review(current):
                gate_reviewers = sm.get_reviewers(current)
                matched_roles = [r for r in user_roles if r in gate_reviewers]
                if matched_roles or "admin" in user_roles:
                    gate_status = rg.get_gate_status(p.dir, current)
                    if gate_status != "approved":
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
                            gate_type="agent_review",
                            status=gate_status,
                            reviewers_required=gate_reviewers,
                            decided_reviewers=decided,
                        ))
            continue

        # human_audit 门
        gate_reviewers = sm.get_reviewers(current)
        matched_roles = [r for r in user_roles if r in gate_reviewers]
        if not matched_roles and "admin" not in user_roles:
            continue

        gate_status = rg.get_gate_status(p.dir, current)
        if gate_status == "approved":
            continue

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
            gate_type="human_audit",
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
    """获取评审详情"""
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

    gate_type = sm.get_gate_type(gate_name) or "human_audit"

    # 检查清单（仅人审门从 pipeline 获取，Agent评门从 skill 获取）
    checklist = []
    review_input = None
    if gate_name in sm.pipeline.review_gates:
        gate_def = sm.pipeline.review_gates[gate_name]
        if gate_type == "human_audit":
            checklist = gate_def.checklist
        review_input = gate_def.review_input

    return ReviewDetail(
        project_name=project_name,
        gate_name=gate_name,
        gate_type=gate_type,
        status=record.status,
        reviewers_required=record.reviewers_required,
        decisions=[d.model_dump() for d in record.decisions],
        checklist=checklist,
        review_input=review_input,
    )


@router.post("/{project_name}/{gate_name}")
async def submit_review(
    project_name: str,
    gate_name: str,
    req: ReviewSubmitRequest,
    user: User = Depends(get_current_user),
):
    """提交人审决定 (仅 human_audit 门)"""
    sm = StateMachine()

    # Agent评审门不接受人工审批
    if sm.is_agent_review(gate_name):
        raise HTTPException(status_code=400, detail="此评审门为Agent评审，不接受人工审批。请通过触发Agent评审来执行。")

    user_roles = [rb.role for rb in user.roles]
    rg = ReviewGate(sm)

    gate_reviewers = sm.get_reviewers(gate_name)
    matched_roles = [r for r in user_roles if r in gate_reviewers]
    if not matched_roles and "admin" not in user_roles:
        raise HTTPException(status_code=403, detail="无权参与此评审")

    try:
        p = Project.load(project_name)
    except Exception:
        raise HTTPException(status_code=404, detail="项目不存在")

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
            if sm.is_interrupt_point(next_state):
                rg.create_review(p.dir, project_name, next_state)
    elif record.status == "rejected":
        next_state = sm.get_next_state(gate_name, "review_rejected")
        if next_state:
            p.transition_to(next_state)

    return {
        "gate_name": gate_name,
        "gate_type": "human_audit",
        "status": record.status,
        "reviewer": reviewer_role,
    }


@router.post("/{project_name}/{gate_name}/trigger-agent-review")
async def trigger_agent_review(
    project_name: str,
    gate_name: str,
    user: User = Depends(require_admin),
):
    """触发Agent评审（管理员手动触发或系统调用）

    此端点创建评审记录，实际 Agent 执行由 Hermes 集成完成。
    """
    sm = StateMachine()

    if not sm.is_agent_review(gate_name):
        raise HTTPException(status_code=400, detail="此评审门不是Agent评审类型")

    try:
        p = Project.load(project_name)
    except Exception:
        raise HTTPException(status_code=404, detail="项目不存在")

    rg = ReviewGate(sm)

    # 创建评审记录（如尚未创建）
    gate_status = rg.get_gate_status(p.dir, gate_name)
    if gate_status == "not_created":
        rg.create_review(p.dir, project_name, gate_name)

    # 返回评审信息供后续 Agent 执行
    review_input = sm.get_review_input(gate_name)
    reviewers = sm.get_reviewers(gate_name)

    return {
        "gate_name": gate_name,
        "gate_type": "agent_review",
        "status": "awaiting_review",
        "reviewers": reviewers,
        "review_input": review_input,
        "message": "评审记录已创建。Agent 执行待 Hermes 集成完成后自动触发。",
    }
