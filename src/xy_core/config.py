"""工作区路径与全局配置"""

import os
from pathlib import Path

WORKSPACE = Path(os.environ.get("XY_WORKSPACE", str(Path(__file__).resolve().parents[2])))

PROJECTS_DIR = WORKSPACE / "projects"
AGENTS_DIR = WORKSPACE / "agents"
TEMPLATE_DIR = WORKSPACE / "templates" / "project"
PIPELINE_CONFIG = WORKSPACE / "config" / "pipeline.yaml"


def validate_workspace() -> None:
    """启动时校验工作区完整性"""
    if not WORKSPACE.exists():
        raise RuntimeError(f"工作区不存在: {WORKSPACE}")
    if not PIPELINE_CONFIG.exists():
        raise RuntimeError(f"流水线配置缺失: {PIPELINE_CONFIG}")
    if not AGENTS_DIR.exists():
        raise RuntimeError(f"Agent目录缺失: {AGENTS_DIR}")
    PROJECTS_DIR.mkdir(exist_ok=True)
