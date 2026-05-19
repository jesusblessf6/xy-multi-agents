"""项目 CRUD — 文件系统操作，线程安全"""

import fcntl
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional

from .config import AGENTS_DIR, PROJECTS_DIR, TEMPLATE_DIR
from .exceptions import ArtifactNotReady, ProjectAlreadyExists, ProjectNotFound
from .types import ProjectMeta, ProjectState, StateTransition


class Project:
    """单个项目实例"""

    def __init__(self, project_dir: Path):
        self.dir = project_dir
        self.state_file = project_dir / "state.json"
        self.meta_file = project_dir / "meta.json"
        self._state: ProjectState | None = None
        self._meta: ProjectMeta | None = None

    @classmethod
    def create(cls, name: str, client: str = "", description: str = "",
               priority: str = "normal", deadline: str = "", owner: str = "") -> "Project":
        project_dir = PROJECTS_DIR / name
        if project_dir.exists():
            raise ProjectAlreadyExists(f"项目 {name} 已存在")

        shutil.copytree(TEMPLATE_DIR, project_dir)

        meta = ProjectMeta(
            project_name=name,
            client=client,
            description=description,
            priority=priority,
            deadline=deadline,
            owner=owner,
            created_at=datetime.now().isoformat(),
        )

        project = cls(project_dir)
        project._save_json(project.meta_file, meta.model_dump())

        state = project.state
        state.project_name = name
        state.created_at = datetime.now().isoformat()
        project._save_state(state)

        return project

    @classmethod
    def create_with_requirement(cls, name: str, requirement_text: str,
                                client: str = "", description: str = "",
                                priority: str = "normal", deadline: str = "",
                                owner: str = "") -> "Project":
        """创建项目并写入原始需求，项目停留在 idle 状态，等待售前 Agent 处理"""
        project = cls.create(name, client=client, description=description,
                             priority=priority, deadline=deadline, owner=owner)

        raw_dir = project.dir / "00_raw_input"
        raw_dir.mkdir(exist_ok=True)
        (raw_dir / "raw_requirement.md").write_text(requirement_text)

        return project

    @classmethod
    def load(cls, name: str) -> "Project":
        project_dir = PROJECTS_DIR / name
        if not project_dir.exists():
            raise ProjectNotFound(f"项目 {name} 不存在")
        return cls(project_dir)

    @classmethod
    def list_projects(cls) -> list[str]:
        """列出所有项目名"""
        if not PROJECTS_DIR.exists():
            return []
        return sorted(
            d.name for d in PROJECTS_DIR.iterdir()
            if d.is_dir() and (d / "state.json").exists()
        )

    @property
    def state(self) -> ProjectState:
        if self._state is None:
            self._state = ProjectState(**self._load_json(self.state_file))
        return self._state

    @property
    def meta(self) -> ProjectMeta:
        if self._meta is None:
            self._meta = ProjectMeta(**self._load_json(self.meta_file))
        return self._meta

    @property
    def current_state(self) -> str:
        return self.state.current_state

    def transition_to(self, new_state: str) -> None:
        state = self.state
        state.states_history.append(StateTransition(
            **{"from": state.current_state, "to": new_state,
               "timestamp": datetime.now().isoformat()}
        ))
        state.current_state = new_state
        self._save_state(state)

    def update_artifact_status(self, artifact_name: str, status: str, produced_by: str = "") -> None:
        state = self.state
        if artifact_name in state.artifacts:
            state.artifacts[artifact_name].status = status
            if produced_by:
                state.artifacts[artifact_name].produced_by = produced_by
            self._save_state(state)

    def update_review_status(self, review_name: str, status: str, comments: str = "") -> None:
        state = self.state
        if review_name in state.reviews:
            state.reviews[review_name] = {
                "status": status,
                "comments": comments,
                "timestamp": datetime.now().isoformat(),
            }
            self._save_state(state)

    def get_artifact_path(self, artifact_name: str) -> Path:
        state = self.state
        if artifact_name in state.artifacts:
            return self.dir / state.artifacts[artifact_name].path
        raise KeyError(f"未知产出物: {artifact_name}")

    def get_artifact_content(self, artifact_name: str) -> str:
        """读取产出物文件内容"""
        path = self.get_artifact_path(artifact_name)
        if not path.exists():
            raise ArtifactNotReady(f"产出物不存在: {artifact_name}")
        return path.read_text()

    def check_artifact_ready(self, artifact_name: str) -> bool:
        path = self.get_artifact_path(artifact_name)
        if path.is_file():
            return path.stat().st_size > 0
        if path.is_dir():
            return any(path.iterdir())
        return False

    def _save_state(self, state: ProjectState) -> None:
        self._save_json(self.state_file, state.model_dump())
        self._state = state

    def _load_json(self, path: Path) -> dict:
        with open(path) as f:
            fcntl.flock(f, fcntl.LOCK_SH)
            try:
                return json.load(f)
            finally:
                fcntl.flock(f, fcntl.LOCK_UN)

    def _save_json(self, path: Path, data: dict) -> None:
        with open(path, "w") as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            try:
                json.dump(data, f, indent=2, ensure_ascii=False)
            finally:
                fcntl.flock(f, fcntl.LOCK_UN)
