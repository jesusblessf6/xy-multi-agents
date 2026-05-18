"""评审门生命周期 — 多审核人、JSON+MD 双格式持久化"""

import json
from datetime import datetime
from pathlib import Path

from .exceptions import ReviewGateError
from .pipeline import load_pipeline
from .state_machine import StateMachine
from .types import PipelineDef, ReviewRecord, ReviewerDecision


class ReviewGate:
    """评审门管理器

    - 多审核人：每人独立提交决定，全部通过才放行
    - 评审记录存 projects/<name>/reviews/<gate>.json（机器可读）
    - 同时生成 .md 文件供人阅读
    """

    def __init__(self, state_machine: StateMachine | None = None):
        self._sm = state_machine or StateMachine()

    def create_review(self, project_dir: Path, project_name: str,
                      gate_name: str) -> ReviewRecord:
        """初始化评审记录"""
        reviewers = self._sm.get_reviewers(gate_name)
        record = ReviewRecord(
            gate_name=gate_name,
            project_name=project_name,
            status="awaiting_review",
            reviewers_required=reviewers,
        )

        self._save_record(project_dir, record)
        self._generate_md(project_dir, gate_name, record)
        return record

    def submit_decision(self, project_dir: Path, gate_name: str,
                        reviewer_role: str, approved: bool,
                        comments: str = "") -> ReviewRecord:
        """提交一个审核人的决定"""
        record = self.load_record(project_dir, gate_name)

        if record.status != "awaiting_review":
            raise ReviewGateError(f"评审 {gate_name} 已结束，状态: {record.status}")

        if reviewer_role not in record.reviewers_required:
            raise ReviewGateError(f"角色 {reviewer_role} 无权参与 {gate_name} 评审")

        # 检查是否已提交
        existing_roles = {d.reviewer_role for d in record.decisions}
        if reviewer_role in existing_roles:
            raise ReviewGateError(f"角色 {reviewer_role} 已提交过评审决定")

        record.decisions.append(ReviewerDecision(
            reviewer_role=reviewer_role,
            approved=approved,
            comments=comments,
            timestamp=datetime.now().isoformat(),
        ))

        # 检查是否所有审核人都已提交
        decided_roles = {d.reviewer_role for d in record.decisions}
        all_decided = all(r in decided_roles for r in record.reviewers_required)

        if all_decided:
            any_rejected = any(not d.approved for d in record.decisions)
            if any_rejected:
                record.status = "rejected"
            else:
                record.status = "approved"
            record.resolved_at = datetime.now().isoformat()

        self._save_record(project_dir, record)
        self._generate_md(project_dir, gate_name, record)
        return record

    def get_gate_status(self, project_dir: Path, gate_name: str) -> str:
        """获取评审门状态: awaiting_review / approved / rejected / not_created"""
        record_path = project_dir / "reviews" / f"{gate_name}.json"
        if not record_path.exists():
            return "not_created"
        record = self.load_record(project_dir, gate_name)
        return record.status

    def is_gate_resolved(self, project_dir: Path, gate_name: str) -> bool:
        """评审门是否已有结果"""
        status = self.get_gate_status(project_dir, gate_name)
        return status in ("approved", "rejected")

    def load_record(self, project_dir: Path, gate_name: str) -> ReviewRecord:
        """加载评审记录"""
        record_path = project_dir / "reviews" / f"{gate_name}.json"
        if not record_path.exists():
            raise ReviewGateError(f"评审记录不存在: {gate_name}")
        with open(record_path) as f:
            data = json.load(f)
        return ReviewRecord(**data)

    def _save_record(self, project_dir: Path, record: ReviewRecord) -> None:
        """保存 JSON 评审记录"""
        reviews_dir = project_dir / "reviews"
        reviews_dir.mkdir(exist_ok=True)
        record_path = reviews_dir / f"{record.gate_name}.json"
        with open(record_path, "w") as f:
            json.dump(record.model_dump(), f, indent=2, ensure_ascii=False)

    def _generate_md(self, project_dir: Path, gate_name: str,
                     record: ReviewRecord) -> None:
        """生成人可读的评审 Markdown 文档"""
        reviews_dir = project_dir / "reviews"
        reviews_dir.mkdir(exist_ok=True)
        md_path = reviews_dir / f"{gate_name}.md"

        # 获取检查清单
        checklist = []
        if gate_name in self._sm.pipeline.review_gates:
            gate_def = self._sm.pipeline.review_gates[gate_name]
            checklist = gate_def.checklist

        lines = [
            f"# {gate_name} 评审",
            f"",
            f"**项目**: {record.project_name}",
            f"**状态**: {record.status}",
            f"**创建时间**: {record.created_at}",
            f"",
            "## 审核人",
        ]
        for r in record.reviewers_required:
            lines.append(f"- {r}")

        if checklist:
            lines.append("")
            lines.append("## 评审检查清单")
            for item in checklist:
                lines.append(f"- [ ] {item}")

        if record.decisions:
            lines.append("")
            lines.append("## 评审结果")
            for d in record.decisions:
                verdict = "通过" if d.approved else "驳回"
                lines.append(f"- **{d.reviewer_role}**: {verdict}")
                if d.comments:
                    lines.append(f"  > {d.comments}")

        lines.append("")
        lines.append("---")
        lines.append("*此文档由 XY Multi-Agents 系统自动生成*")

        md_path.write_text("\n".join(lines))
