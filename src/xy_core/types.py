"""核心数据模型 — Pydantic v2"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


# ── 项目 ──────────────────────────────────────


class ArtifactInfo(BaseModel):
    status: str = "pending"
    path: str
    produced_by: str = ""


class ReviewInfo(BaseModel):
    status: str = "pending"
    comments: str = ""
    timestamp: str = ""


class ProjectMeta(BaseModel):
    project_name: str = ""
    client: str = ""
    description: str = ""
    priority: str = "normal"
    deadline: str = ""
    created_at: str = ""
    owner: str = ""


class StateTransition(BaseModel):
    from_state: str = Field(alias="from")
    to_state: str = Field(alias="to")
    timestamp: str = ""

    model_config = {"populate_by_name": True}


class ProjectState(BaseModel):
    project_name: str = ""
    created_at: str = ""
    current_state: str = "idle"
    states_history: list[StateTransition] = []
    artifacts: dict[str, ArtifactInfo] = {}
    reviews: dict[str, ReviewInfo] = {}


# ── Pipeline ──────────────────────────────────


class PipelineStateConfig(BaseModel):
    description: str = ""
    type: str = "agent_execution"
    gate_type: Optional[str] = None  # "human_audit" | "agent_review"，仅 type=review_gate 时有效
    agent: Optional[str] = None
    agents: Optional[list[str]] = None
    next: list[str] = []
    next_approved: list[str] = []
    next_rejected: list[str] = []
    trigger: str = ""
    output_check: list[str] = []
    reviewers: list[str] = []
    review_input: Optional[str] = None  # agent_review 门的输入产出物路径
    output: str = ""

    @field_validator("output_check", mode="before")
    @classmethod
    def coerce_output_check(cls, v):
        if isinstance(v, str):
            return [v]
        return v


class ReviewerDef(BaseModel):
    role: str
    focus: str = ""  # deprecated: 迁移到 agent skill


class ReviewGateDef(BaseModel):
    name: str
    description: str = ""
    gate_type: str = "human_audit"  # "human_audit" | "agent_review"
    reviewers: list[ReviewerDef] = []
    checklist: list[str] = []  # deprecated: 人审门可保留用于 UI 展示，agent_review 门迁移到 skill
    review_input: Optional[str] = None  # agent_review 门的输入产出物路径


class PipelineDef(BaseModel):
    states: dict[str, PipelineStateConfig]
    review_gates: dict[str, ReviewGateDef] = {}


# ── Agent ─────────────────────────────────────


class AgentConfig(BaseModel):
    name: str
    display_name: str = ""
    role: str = ""
    responsibilities: list[str] = []
    inputs: list[str] = []
    outputs: list[dict[str, str] | str] = []
    output_dir: str = ""
    skills_dir: str = ""
    rag_dir: str = ""
    review_gate: Optional[str | dict] = None  # deprecated: pipeline.yaml 是评审门唯一真相源
    prompt_template: str = ""
    is_orchestrator: bool = False


# ── Skill ─────────────────────────────────────


class SkillDef(BaseModel):
    name: str
    description: str = ""
    allowed_tools: list[str] = []
    content: str = ""


class SkillSummary(BaseModel):
    """渐进式注入 — 仅摘要，不含正文"""
    name: str
    description: str = ""
    allowed_tools: list[str] = []
    file_path: str = ""


# ── RAG ───────────────────────────────────────


class RagDoc(BaseModel):
    name: str
    file_path: str = ""
    content: str = ""


# ── 评审 ──────────────────────────────────────


class AgentReviewResult(BaseModel):
    """Agent 评审的结构化输出"""
    reviewer_role: str
    gate_name: str
    verdict: str  # "approve" | "reject" | "conditional_approve"
    summary: str
    findings: list[dict] = []  # [{"item": "...", "severity": "critical|major|minor", "detail": "..."}]
    recommendations: list[str] = []
    conditions: list[str] = []  # conditional_approve 时必须的修改项


class ReviewerDecision(BaseModel):
    reviewer_role: str
    approved: bool
    comments: str = ""
    decision_type: str = "human"  # "human" | "agent"
    review_result: Optional[AgentReviewResult] = None
    timestamp: str = ""


class ReviewRecord(BaseModel):
    gate_name: str
    project_name: str
    status: str = "awaiting_review"
    reviewers_required: list[str] = []
    decisions: list[ReviewerDecision] = []
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    resolved_at: str = ""


# ── 状态机事件 ────────────────────────────────


class TransitionEvent(BaseModel):
    event: str  # artifacts_ready | review_approved | review_rejected
    data: dict = {}
