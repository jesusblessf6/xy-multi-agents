"""核心引擎单元测试"""

import json
import shutil
import tempfile
import uuid
from pathlib import Path

import pytest
import yaml

from xy_core.config import AGENTS_DIR, PIPELINE_CONFIG
from xy_core.pipeline import get_graph_structure, load_pipeline
from xy_core.state_machine import StateMachine
from xy_core.project import Project
from xy_core.artifact import check_artifacts_ready
from xy_core.review_gate import ReviewGate
from xy_core.agent_registry import (
    list_agents, load_agent_config, get_skill_summaries,
    validate_skill_frontmatter, _parse_frontmatter,
)
from xy_core.agent_executor import (
    build_agent_prompt, build_delegate_request, build_review_prompt,
    build_review_delegate_request, load_upstream_artifacts,
)
from xy_core.types import AgentReviewResult
from xy_core.exceptions import (
    InvalidStateTransition, ProjectAlreadyExists, ProjectNotFound,
    ReviewGateError, SkillFormatError,
)


def _uid(prefix: str = "test") -> str:
    """生成唯一项目名，避免并发测试冲突"""
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


# ── Pipeline ──────────────────────────────────


class TestPipeline:
    def test_load_pipeline(self):
        pipeline = load_pipeline()
        assert "states" in pipeline.model_dump()
        assert "idle" in pipeline.states
        assert "delivery" in pipeline.states

    def test_pipeline_has_review_gates(self):
        pipeline = load_pipeline()
        review_states = [n for n, c in pipeline.states.items() if c.type == "review_gate"]
        assert len(review_states) == 6
        assert set(review_states) == {"req_audit", "req_feasibility", "prd_review", "design_review", "arch_review", "test_review"}

    def test_graph_structure(self):
        pipeline = load_pipeline()
        graph = get_graph_structure(pipeline)
        assert len(graph["nodes"]) == 15
        assert len(graph["edges"]) > 0
        node_ids = {n["id"] for n in graph["nodes"]}
        assert "idle" in node_ids
        assert "delivery" in node_ids


# ── State Machine ─────────────────────────────


class TestStateMachine:
    def setup_method(self):
        self.sm = StateMachine()

    def test_interrupt_points_only_human_audit(self):
        """中断点只包含 human_audit 门"""
        points = self.sm.get_interrupt_points()
        assert "req_audit" in points
        # agent_review 门不是中断点
        assert "req_feasibility" not in points
        assert "prd_review" not in points
        assert "arch_review" not in points
        assert "idle" not in points

    def test_is_interrupt_point(self):
        assert self.sm.is_interrupt_point("req_audit")
        assert not self.sm.is_interrupt_point("req_feasibility")
        assert not self.sm.is_interrupt_point("prd")

    def test_gate_type(self):
        assert self.sm.get_gate_type("req_audit") == "human_audit"
        assert self.sm.get_gate_type("req_feasibility") == "agent_review"
        assert self.sm.get_gate_type("prd_review") == "agent_review"
        assert self.sm.get_gate_type("idle") is None

    def test_is_human_audit(self):
        assert self.sm.is_human_audit("req_audit")
        assert not self.sm.is_human_audit("req_feasibility")

    def test_is_agent_review(self):
        assert self.sm.is_agent_review("req_feasibility")
        assert self.sm.is_agent_review("prd_review")
        assert not self.sm.is_agent_review("req_audit")

    def test_review_input(self):
        assert self.sm.get_review_input("req_feasibility") == "01_requirements/requirements.md"
        assert self.sm.get_review_input("prd_review") == "02_prd/prd.md"
        assert self.sm.get_review_input("req_audit") is None

    def test_get_next_state_agent_execution(self):
        next_state = self.sm.get_next_state("idle", "artifacts_ready")
        assert next_state == "requirements"

    def test_get_next_state_review_approved(self):
        next_state = self.sm.get_next_state("prd_review", "review_approved")
        assert next_state == "design"

    def test_get_next_state_review_rejected(self):
        next_state = self.sm.get_next_state("prd_review", "review_rejected")
        assert next_state == "prd"

    def test_invalid_event_on_review_gate(self):
        with pytest.raises(InvalidStateTransition):
            self.sm.get_next_state("prd_review", "artifacts_ready")

    def test_req_audit_flow(self):
        next_state = self.sm.get_next_state("req_audit", "review_approved")
        assert next_state == "req_feasibility"
        next_state = self.sm.get_next_state("req_audit", "review_rejected")
        assert next_state == "requirements"

    def test_req_feasibility_flow(self):
        next_state = self.sm.get_next_state("req_feasibility", "review_approved")
        assert next_state == "prd"
        next_state = self.sm.get_next_state("req_feasibility", "review_rejected")
        assert next_state == "requirements"

    def test_req_audit_reviewers(self):
        reviewers = self.sm.get_reviewers("req_audit")
        assert reviewers == ["presales"]

    def test_req_feasibility_reviewers(self):
        reviewers = self.sm.get_reviewers("req_feasibility")
        assert set(reviewers) == {"product", "architect"}

    def test_terminal_state(self):
        assert self.sm.is_terminal("delivery")
        assert self.sm.get_next_state("delivery", "artifacts_ready") is None

    def test_parallel_agents(self):
        agents = self.sm.get_parallel_agents("development")
        assert agents == ["frontend", "backend"]

    def test_get_reviewers(self):
        reviewers = self.sm.get_reviewers("prd_review")
        assert "product" in reviewers
        assert "architect" in reviewers

    def test_get_output_check(self):
        checks = self.sm.get_output_check("prd")
        assert "02_prd/prd.md" in checks
        assert "02_prd/prototype.md" in checks

    def test_rejected_target(self):
        target = self.sm.get_rejected_target("prd_review")
        assert target == "prd"


# ── Project ───────────────────────────────────


class TestProject:
    def setup_method(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        self.projects_dir = self.tmpdir / "projects"
        self.projects_dir.mkdir()
        self.template_dir = self.tmpdir / "templates" / "project"
        self.template_dir.mkdir(parents=True)

        real_template = Path(__file__).resolve().parents[1] / "templates" / "project"
        shutil.copytree(real_template, self.template_dir, dirs_exist_ok=True)

        import xy_core.config as cfg
        self._orig_projects = cfg.PROJECTS_DIR
        self._orig_template = cfg.TEMPLATE_DIR
        cfg.PROJECTS_DIR = self.projects_dir
        cfg.TEMPLATE_DIR = self.template_dir

    def teardown_method(self):
        import xy_core.config as cfg
        cfg.PROJECTS_DIR = self._orig_projects
        cfg.TEMPLATE_DIR = self._orig_template
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_create_project(self):
        p = Project.create(_uid("create"), client="ACME")
        assert p.dir.exists()
        assert p.current_state == "idle"

    def test_create_duplicate_project(self):
        name = _uid("dup")
        Project.create(name)
        with pytest.raises(ProjectAlreadyExists):
            Project.create(name)

    def test_create_with_requirement(self):
        p = Project.create_with_requirement(_uid("req"), "需求描述")
        assert p.current_state == "idle"
        raw_path = p.dir / "00_raw_input" / "raw_requirement.md"
        assert raw_path.exists()
        assert raw_path.read_text() == "需求描述"

    def test_load_project(self):
        name = _uid("load")
        Project.create(name)
        p = Project.load(name)
        assert p.meta.project_name == name

    def test_load_nonexistent(self):
        with pytest.raises(ProjectNotFound):
            Project.load("no-such-proj-xyz")

    def test_transition(self):
        p = Project.create(_uid("trans"))
        p.transition_to("requirements")
        assert p.current_state == "requirements"
        assert len(p.state.states_history) == 1

    def test_list_projects(self):
        Project.create(_uid("a"))
        Project.create(_uid("b"))
        names = Project.list_projects()
        assert len(names) >= 2


# ── Agent Registry ────────────────────────────


class TestAgentRegistry:
    def test_list_agents(self):
        agents = list_agents()
        assert len(agents) == 8
        assert "product" in agents

    def test_load_agent_config(self):
        config = load_agent_config("product")
        assert config.name == "product"
        assert config.display_name == "产品Agent"
        assert "requirements.md" in config.inputs

    def test_get_skill_summaries_with_review_skills(self):
        """产品Agent应有评审skill"""
        summaries = get_skill_summaries("product")
        assert isinstance(summaries, list)
        assert len(summaries) > 0
        skill_names = [s.name for s in summaries]
        assert "req_feasibility_review" in skill_names
        assert "prd_review" in skill_names

    def test_get_skill_summaries_architect(self):
        summaries = get_skill_summaries("architect")
        skill_names = [s.name for s in summaries]
        assert "req_feasibility_review" in skill_names
        assert "arch_review" in skill_names

    def test_parse_frontmatter(self):
        content = "---\nname: test-skill\ndescription: A test\nallowed-tools: [file]\n---\n\nBody here\n"
        meta, body = _parse_frontmatter(content)
        assert meta["name"] == "test-skill"
        assert "Body here" in body

    def test_parse_frontmatter_missing(self):
        content = "Just plain markdown"
        meta, body = _parse_frontmatter(content)
        assert meta == {}
        assert body == content

    def test_validate_skill_frontmatter_valid(self):
        content = "---\nname: test\ndescription: desc\n---\n\nBody\n"
        valid, error = validate_skill_frontmatter(content)
        assert valid
        assert error == ""

    def test_validate_skill_frontmatter_missing_field(self):
        content = "---\nname: test\n---\n\nBody\n"
        valid, error = validate_skill_frontmatter(content)
        assert not valid
        assert "description" in error

    def test_validate_skill_frontmatter_empty_body(self):
        content = "---\nname: test\ndescription: desc\n---\n\n"
        valid, error = validate_skill_frontmatter(content)
        assert not valid


# ── Review Gate ───────────────────────────────


class TestReviewGate:
    def setup_method(self):
        self.sm = StateMachine()
        self.rg = ReviewGate(self.sm)
        self.tmpdir = Path(tempfile.mkdtemp())
        (self.tmpdir / "reviews").mkdir()

    def teardown_method(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_create_review(self):
        record = self.rg.create_review(self.tmpdir, "test-proj", "prd_review")
        assert record.status == "awaiting_review"
        assert "product" in record.reviewers_required
        assert "architect" in record.reviewers_required
        assert (self.tmpdir / "reviews" / "prd_review.json").exists()
        assert (self.tmpdir / "reviews" / "prd_review.md").exists()

    def test_submit_decision_single(self):
        self.rg.create_review(self.tmpdir, "test-proj", "prd_review")
        record = self.rg.submit_decision(self.tmpdir, "prd_review", "product", True, "OK")
        assert record.status == "awaiting_review"

    def test_submit_decision_all_approved(self):
        self.rg.create_review(self.tmpdir, "test-proj", "prd_review")
        self.rg.submit_decision(self.tmpdir, "prd_review", "product", True)
        record = self.rg.submit_decision(self.tmpdir, "prd_review", "architect", True)
        assert record.status == "approved"

    def test_submit_decision_rejected(self):
        self.rg.create_review(self.tmpdir, "test-proj", "prd_review")
        self.rg.submit_decision(self.tmpdir, "prd_review", "product", True)
        record = self.rg.submit_decision(self.tmpdir, "prd_review", "architect", False, "需修改")
        assert record.status == "rejected"

    def test_submit_decision_wrong_reviewer(self):
        self.rg.create_review(self.tmpdir, "test-proj", "prd_review")
        with pytest.raises(ReviewGateError, match="无权参与"):
            self.rg.submit_decision(self.tmpdir, "prd_review", "design", True)

    def test_submit_decision_duplicate(self):
        self.rg.create_review(self.tmpdir, "test-proj", "prd_review")
        self.rg.submit_decision(self.tmpdir, "prd_review", "product", True)
        with pytest.raises(ReviewGateError, match="已提交过"):
            self.rg.submit_decision(self.tmpdir, "prd_review", "product", True)

    def test_submit_agent_review(self):
        """Agent评审提交"""
        self.rg.create_review(self.tmpdir, "test-proj", "req_feasibility")
        result = AgentReviewResult(
            reviewer_role="product",
            gate_name="req_feasibility",
            verdict="approve",
            summary="需求范围合理",
            findings=[],
            recommendations=[],
            conditions=[],
        )
        record = self.rg.submit_agent_review(self.tmpdir, "req_feasibility", result)
        assert record.status == "awaiting_review"
        assert len(record.decisions) == 1
        assert record.decisions[0].decision_type == "agent"
        assert record.decisions[0].approved is True

    def test_submit_agent_review_all_approved(self):
        """所有Agent评审通过"""
        self.rg.create_review(self.tmpdir, "test-proj", "req_feasibility")
        result1 = AgentReviewResult(
            reviewer_role="product", gate_name="req_feasibility",
            verdict="approve", summary="OK",
        )
        self.rg.submit_agent_review(self.tmpdir, "req_feasibility", result1)
        result2 = AgentReviewResult(
            reviewer_role="architect", gate_name="req_feasibility",
            verdict="approve", summary="可行",
        )
        record = self.rg.submit_agent_review(self.tmpdir, "req_feasibility", result2)
        assert record.status == "approved"

    def test_submit_agent_review_rejected(self):
        """Agent评审驳回"""
        self.rg.create_review(self.tmpdir, "test-proj", "req_feasibility")
        result1 = AgentReviewResult(
            reviewer_role="product", gate_name="req_feasibility",
            verdict="approve", summary="OK",
        )
        self.rg.submit_agent_review(self.tmpdir, "req_feasibility", result1)
        result2 = AgentReviewResult(
            reviewer_role="architect", gate_name="req_feasibility",
            verdict="reject", summary="成本超预期",
            findings=[{"item": "成本过高", "severity": "critical", "detail": "超出预期50%"}],
        )
        record = self.rg.submit_agent_review(self.tmpdir, "req_feasibility", result2)
        assert record.status == "rejected"

    def test_parse_agent_review_output(self):
        """解析Agent评审输出的结构化块"""
        reviews_dir = self.tmpdir / "reviews"
        review_md = reviews_dir / "req_feasibility_product.md"
        review_md.write_text("""# 需求可行性评审

## 总评
需求范围合理，MVP边界清晰。

## 发现项
- [minor] 非功能需求描述不够具体

## 结论
approve

<!-- review_result
verdict: approve
summary: 需求范围合理，MVP边界清晰
findings:
  - item: "非功能需求描述不够具体"
    severity: minor
    detail: "性能指标缺少量化数据"
recommendations:
  - "补充具体的性能指标要求"
conditions: []
-->
""")
        result = self.rg.parse_agent_review_output(self.tmpdir, "req_feasibility", "product")
        assert result.verdict == "approve"
        assert result.summary == "需求范围合理，MVP边界清晰"
        assert len(result.findings) == 1
        assert result.findings[0]["severity"] == "minor"


# ── Artifact ──────────────────────────────────


class TestArtifact:
    def setup_method(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        self.projects_dir = self.tmpdir / "projects"
        self.template_dir = self.tmpdir / "templates" / "project"
        self.projects_dir.mkdir()
        self.template_dir.mkdir(parents=True)

        real_template = Path(__file__).resolve().parents[1] / "templates" / "project"
        shutil.copytree(real_template, self.template_dir, dirs_exist_ok=True)

        import xy_core.config as cfg
        self._orig_projects = cfg.PROJECTS_DIR
        self._orig_template = cfg.TEMPLATE_DIR
        cfg.PROJECTS_DIR = self.projects_dir
        cfg.TEMPLATE_DIR = self.template_dir

    def teardown_method(self):
        import xy_core.config as cfg
        cfg.PROJECTS_DIR = self._orig_projects
        cfg.TEMPLATE_DIR = self._orig_template
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_check_artifacts_not_ready(self):
        p = Project.create(_uid("art"))
        p.transition_to("requirements")
        sm = StateMachine()
        result = check_artifacts_ready(p, sm)
        assert not result["ready"]

    def test_check_artifacts_ready(self):
        p = Project.create_with_requirement(_uid("art2"), "需求内容")
        sm = StateMachine()
        result = check_artifacts_ready(p, sm)
        assert result["ready"]


# ── Agent Executor ────────────────────────────


class TestAgentExecutor:
    def test_build_agent_prompt(self):
        config = load_agent_config("product")
        prompt = build_agent_prompt(
            config, project_dir=Path("/tmp/nonexistent-proj"),
            project_name="test-proj", current_state="prd",
        )
        assert "产品Agent" in prompt
        assert "02_prd" in prompt

    def test_build_delegate_request(self):
        config = load_agent_config("product")
        req = build_delegate_request(
            config, project_dir=Path("/tmp/nonexistent-proj"),
            project_name="test-proj", current_state="prd",
        )
        assert "goal" in req
        assert "context" in req
        assert "toolsets" in req

    def test_load_upstream_artifacts_empty_dir(self):
        config = load_agent_config("product")
        tmpdir = Path(tempfile.mkdtemp())
        artifacts = load_upstream_artifacts(tmpdir, config)
        assert "requirements.md" in artifacts
        assert "不存在" in artifacts["requirements.md"]
        shutil.rmtree(tmpdir)

    def test_build_review_prompt(self):
        """评审 prompt 构建测试"""
        config = load_agent_config("product")
        prompt = build_review_prompt(
            config, project_dir=Path("/tmp/nonexistent-proj"),
            project_name="test-proj", gate_name="req_feasibility",
            review_input_path="01_requirements/requirements.md",
        )
        assert "评审任务" in prompt
        assert "req_feasibility" in prompt
        assert "req_feasibility_review" in prompt  # skill 名称

    def test_build_review_delegate_request(self):
        config = load_agent_config("product")
        req = build_review_delegate_request(
            config, project_dir=Path("/tmp/nonexistent-proj"),
            project_name="test-proj", gate_name="req_feasibility",
            review_input_path="01_requirements/requirements.md",
        )
        assert "goal" in req
        assert "req_feasibility" in req["goal"]
        assert "context" in req


# ── AgentReviewResult ─────────────────────────


class TestAgentReviewResult:
    def test_valid_result(self):
        result = AgentReviewResult(
            reviewer_role="product",
            gate_name="req_feasibility",
            verdict="approve",
            summary="需求可行",
        )
        assert result.verdict == "approve"
        assert result.findings == []

    def test_with_findings(self):
        result = AgentReviewResult(
            reviewer_role="architect",
            gate_name="req_feasibility",
            verdict="conditional_approve",
            summary="基本可行，需补充",
            findings=[
                {"item": "性能指标缺失", "severity": "major", "detail": "需要QPS数据"},
            ],
            conditions=["补充性能指标"],
        )
        assert result.verdict == "conditional_approve"
        assert len(result.findings) == 1
        assert result.conditions == ["补充性能指标"]
