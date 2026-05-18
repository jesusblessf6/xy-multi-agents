"""产出物就绪检查"""

from pathlib import Path

from .project import Project
from .state_machine import StateMachine


def check_artifacts_ready(project: Project, state_machine: StateMachine) -> dict:
    """检查当前状态所需产出物是否就绪

    Returns:
        {"ready": bool, "missing": list[str], "ready_list": list[str]}
    """
    output_checks = state_machine.get_output_check(project.current_state)
    if not output_checks:
        return {"ready": True, "missing": [], "ready_list": []}

    missing = []
    ready_list = []

    for artifact_path in output_checks:
        full_path = project.dir / artifact_path
        if _is_ready(full_path):
            ready_list.append(artifact_path)
        else:
            missing.append(artifact_path)

    return {"ready": len(missing) == 0, "missing": missing, "ready_list": ready_list}


def _is_ready(path: Path) -> bool:
    """检查单个产出物路径是否就绪"""
    if path.is_file():
        return path.stat().st_size > 0
    if path.is_dir():
        return any(path.iterdir())
    return False
