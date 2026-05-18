"""
XY Multi-Agents 编排引擎

负责：
1. 项目生命周期管理（创建、状态流转）
2. Agent调度（根据状态触发对应Agent）
3. 评审门管理（组织评审、汇总结果）
4. 产出物检查（验证上游产出是否就绪）
"""

import json
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional

import yaml


WORKSPACE = Path(os.environ.get("XY_WORKSPACE", "/Users/wing/myspace/code/xy-multi-agents"))
PROJECTS_DIR = WORKSPACE / "projects"
TEMPLATE_DIR = WORKSPACE / "templates" / "project"
AGENTS_DIR = WORKSPACE / "agents"
PIPELINE_CONFIG = WORKSPACE / "config" / "pipeline.yaml"


def load_pipeline() -> dict:
    """加载pipeline配置"""
    with open(PIPELINE_CONFIG) as f:
        return yaml.safe_load(f)


def load_agent_config(agent_name: str) -> dict:
    """加载Agent配置"""
    config_path = AGENTS_DIR / agent_name / "agent.yaml"
    with open(config_path) as f:
        return yaml.safe_load(f)


class Project:
    """项目实例，管理单个项目的状态和产出"""

    def __init__(self, project_dir: Path):
        self.dir = project_dir
        self.state_file = project_dir / "state.json"
        self.meta_file = project_dir / "meta.json"
        self._state = None
        self._meta = None

    @classmethod
    def create(cls, name: str, client: str = "", description: str = "",
               priority: str = "normal", deadline: str = "", owner: str = "") -> "Project":
        """创建新项目"""
        project_dir = PROJECTS_DIR / name
        if project_dir.exists():
            raise FileExistsError(f"项目 {name} 已存在")

        # 从模板复制目录结构
        shutil.copytree(TEMPLATE_DIR, project_dir)

        # 写入meta
        meta = {
            "project_name": name,
            "client": client,
            "description": description,
            "priority": priority,
            "deadline": deadline,
            "created_at": datetime.now().isoformat(),
            "owner": owner,
        }
        with open(project_dir / "meta.json", "w") as f:
            json.dump(meta, f, indent=2, ensure_ascii=False)

        # 更新state中的项目名
        project = cls(project_dir)
        state = project.state
        state["project_name"] = name
        state["created_at"] = datetime.now().isoformat()
        project._save_state(state)

        return project

    @classmethod
    def load(cls, name: str) -> "Project":
        """加载已有项目"""
        project_dir = PROJECTS_DIR / name
        if not project_dir.exists():
            raise FileNotFoundError(f"项目 {name} 不存在")
        return cls(project_dir)

    @property
    def state(self) -> dict:
        """读取项目状态"""
        if self._state is None:
            with open(self.state_file) as f:
                self._state = json.load(f)
        return self._state

    @property
    def meta(self) -> dict:
        """读取项目元信息"""
        if self._meta is None:
            with open(self.meta_file) as f:
                self._meta = json.load(f)
        return self._meta

    def _save_state(self, state: dict = None):
        """保存项目状态"""
        if state is None:
            state = self._state
        with open(self.state_file, "w") as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
        self._state = state

    @property
    def current_state(self) -> str:
        return self.state["current_state"]

    def transition_to(self, new_state: str):
        """状态流转"""
        state = self.state
        old_state = state["current_state"]
        state["states_history"].append({
            "from": old_state,
            "to": new_state,
            "timestamp": datetime.now().isoformat(),
        })
        state["current_state"] = new_state
        self._save_state(state)

    def update_artifact_status(self, artifact_name: str, status: str):
        """更新产出物状态"""
        state = self.state
        if artifact_name in state["artifacts"]:
            state["artifacts"][artifact_name]["status"] = status
            self._save_state(state)

    def update_review_status(self, review_name: str, status: str, comments: str = ""):
        """更新评审状态"""
        state = self.state
        if review_name in state["reviews"]:
            state["reviews"][review_name] = {
                "status": status,
                "comments": comments,
                "timestamp": datetime.now().isoformat(),
            }
            self._save_state(state)

    def get_artifact_path(self, artifact_name: str) -> Path:
        """获取产出物路径"""
        state = self.state
        if artifact_name in state["artifacts"]:
            return self.dir / state["artifacts"][artifact_name]["path"]
        raise KeyError(f"未知产出物: {artifact_name}")

    def check_artifact_ready(self, artifact_name: str) -> bool:
        """检查产出物是否就绪"""
        path = self.get_artifact_path(artifact_name)
        return path.exists() and (path.is_file() and path.stat().st_size > 0 or path.is_dir() and any(path.iterdir()))


class Orchestrator:
    """编排器，PM Agent的核心逻辑"""

    def __init__(self, project: Project):
        self.project = project
        self.pipeline = load_pipeline()

    def get_current_stage_config(self) -> dict:
        """获取当前阶段的配置"""
        current = self.project.current_state
        return self.pipeline["states"].get(current, {})

    def get_next_agent(self) -> Optional[dict]:
        """根据当前状态判断应该触发哪个Agent"""
        stage = self.get_current_stage_config()

        if not stage:
            return None

        # 评审门状态 - 需要人工审核
        if stage.get("type") == "review_gate":
            return None  # 评审门需要人工介入

        # 获取agent名称
        agent_name = stage.get("agent")
        agents = stage.get("agents")

        if agent_name:
            return {
                "name": agent_name,
                "config": load_agent_config(agent_name),
                "parallel": False,
            }
        elif agents:
            return {
                "name": agents,
                "config": [load_agent_config(a) for a in agents],
                "parallel": True,
            }

        return None

    def check_ready_to_advance(self) -> dict:
        """检查是否可以推进到下一阶段"""
        stage = self.get_current_stage_config()
        output_check = stage.get("output_check", [])

        if not output_check:
            return {"ready": True, "missing": []}

        if isinstance(output_check, str):
            output_check = [output_check]

        missing = []
        for artifact_path in output_check:
            full_path = self.project.dir / artifact_path
            if full_path.is_file():
                if full_path.stat().st_size == 0:
                    missing.append(artifact_path)
            elif full_path.is_dir():
                if not any(full_path.iterdir()):
                    missing.append(artifact_path)
            else:
                missing.append(artifact_path)

        return {"ready": len(missing) == 0, "missing": missing}

    def advance(self) -> str:
        """推进到下一阶段"""
        check = self.check_ready_to_advance()
        if not check["ready"]:
            return f"产出物未就绪: {check['missing']}"

        stage = self.get_current_stage_config()
        next_states = stage.get("next", [])
        if not next_states:
            return "已到达终态，无法推进"

        # 默认推进到第一个next状态
        next_state = next_states[0]
        self.project.transition_to(next_state)
        return f"已推进到: {next_state}"

    def submit_review(self, review_name: str, approved: bool, comments: str = "") -> str:
        """提交评审结果"""
        stage = self.get_current_stage_config()

        if stage.get("type") != "review_gate":
            return "当前状态不是评审门"

        status = "approved" if approved else "revision_needed"
        self.project.update_review_status(review_name, status, comments)

        if approved:
            next_state = stage.get("next_approved", [])[0] if stage.get("next_approved") else None
        else:
            next_state = stage.get("next_rejected", [])[0] if stage.get("next_rejected") else None

        if next_state:
            self.project.transition_to(next_state)
            return f"评审{'通过' if approved else '不通过'}，流转到: {next_state}"

        return "无法确定下一状态"

    def get_status_report(self) -> str:
        """生成项目状态报告"""
        state = self.project.state
        meta = self.project.meta
        lines = [
            f"项目: {meta.get('project_name', 'N/A')}",
            f"客户: {meta.get('client', 'N/A')}",
            f"当前阶段: {state['current_state']}",
            "",
            "产出物状态:",
        ]
        for name, info in state["artifacts"].items():
            lines.append(f"  {name}: {info['status']}")

        lines.append("")
        lines.append("评审状态:")
        for name, info in state["reviews"].items():
            if isinstance(info, dict):
                lines.append(f"  {name}: {info.get('status', 'pending')}")
            else:
                lines.append(f"  {name}: {info}")

        return "\n".join(lines)


def create_project(name: str, **kwargs) -> Project:
    """便捷函数：创建项目"""
    return Project.create(name, **kwargs)


def load_project(name: str) -> Project:
    """便捷函数：加载项目"""
    return Project.load(name)


if __name__ == "__main__":
    # 简单测试
    import sys
    if len(sys.argv) < 2:
        print("Usage: python engine.py <command> [args]")
        print("Commands: create <name>, status <name>, advance <name>")
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd == "create" and len(sys.argv) >= 3:
        p = create_project(sys.argv[2])
        print(f"项目已创建: {p.dir}")
    elif cmd == "status" and len(sys.argv) >= 3:
        p = load_project(sys.argv[2])
        orch = Orchestrator(p)
        print(orch.get_status_report())
    elif cmd == "advance" and len(sys.argv) >= 3:
        p = load_project(sys.argv[2])
        orch = Orchestrator(p)
        result = orch.advance()
        print(result)
    else:
        print(f"未知命令: {cmd}")
