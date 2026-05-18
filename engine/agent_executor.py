"""
Agent执行器

负责：
1. 加载Agent配置和知识（skills + RAG）
2. 构建Agent的prompt（注入上下文、技能、知识）
3. 调用delegate_task执行Agent任务
4. 收集Agent产出并落盘
"""

import json
from pathlib import Path
from typing import Optional

import yaml


WORKSPACE = Path("/Users/wing/myspace/code/xy-multi-agents")
AGENTS_DIR = WORKSPACE / "agents"


def load_agent_config(agent_name: str) -> dict:
    """加载Agent的YAML配置"""
    config_path = AGENTS_DIR / agent_name / "agent.yaml"
    with open(config_path) as f:
        return yaml.safe_load(f)


def load_agent_skills(agent_name: str) -> str:
    """加载Agent的所有skills，合并为一段文本"""
    skills_dir = AGENTS_DIR / agent_name / "skills"
    if not skills_dir.exists():
        return ""

    parts = []
    for skill_file in sorted(skills_dir.glob("*.md")):
        parts.append(f"### Skill: {skill_file.stem}\n\n{skill_file.read_text()}\n")

    return "\n---\n".join(parts) if parts else ""


def load_agent_rag(agent_name: str) -> str:
    """加载Agent的RAG知识库，合并为一段文本"""
    rag_dir = AGENTS_DIR / agent_name / "rag"
    if not rag_dir.exists():
        return ""

    parts = []
    for rag_file in sorted(rag_dir.glob("*.md")):
        parts.append(f"### 知识: {rag_file.stem}\n\n{rag_file.read_text()}\n")

    return "\n---\n".join(parts) if parts else ""


def build_agent_prompt(agent_name: str, project_context: dict, upstream_artifacts: dict = None) -> str:
    """
    构建Agent的完整执行prompt

    Args:
        agent_name: Agent名称
        project_context: 项目上下文（meta + state）
        upstream_artifacts: 上游产出物 {name: content}
    """
    config = load_agent_config(agent_name)
    skills = load_agent_skills(agent_name)
    rag = load_agent_rag(agent_name)

    prompt_parts = []

    # 1. Agent角色和任务
    prompt_parts.append(f"# 你是: {config['display_name']}\n")
    prompt_parts.append(f"## 角色定义\n{config['role']}\n")

    # 2. 项目上下文
    prompt_parts.append("## 项目信息")
    prompt_parts.append(f"项目名: {project_context.get('project_name', 'N/A')}")
    prompt_parts.append(f"当前阶段: {project_context.get('current_state', 'N/A')}\n")

    # 3. 上游产出
    if upstream_artifacts:
        prompt_parts.append("## 上游产出（请仔细阅读）")
        for name, content in upstream_artifacts.items():
            prompt_parts.append(f"### {name}\n{content}\n")

    # 4. Skills
    if skills:
        prompt_parts.append(f"## 你的专业技能\n{skills}\n")

    # 5. RAG知识
    if rag:
        prompt_parts.append(f"## 领域知识库\n{rag}\n")

    # 6. 执行指令
    prompt_parts.append("## 执行指令")
    prompt_parts.append(config["prompt_template"])

    # 7. 产出要求
    prompt_parts.append("\n## 产出要求")
    prompt_parts.append(f"请将你的产出写入项目的 {config['output_dir']} 目录。")
    prompt_parts.append("确保文件内容完整、格式规范。完成后报告产出物清单。")

    return "\n".join(prompt_parts)


def load_upstream_artifacts(project_dir: Path, agent_name: str) -> dict:
    """
    根据Agent的inputs配置，加载上游产出物内容

    Args:
        project_dir: 项目目录
        agent_name: Agent名称
    """
    config = load_agent_config(agent_name)
    inputs = config.get("inputs", [])
    artifacts = {}

    # 输入到文件路径的映射
    input_path_map = {
        "requirements.md": "01_requirements/requirements.md",
        "prd.md": "02_prd/prd.md",
        "prototype.md": "02_prd/prototype.md",
        "design_spec.md": "03_design/design_spec.md",
        "architecture.md": "04_architecture/architecture.md",
        "api_spec.md": "04_architecture/api_spec.md",
        "test_cases.md": "07_test/test_cases.md",
    }

    for input_name in inputs:
        if input_name in input_path_map:
            path = project_dir / input_path_map[input_name]
            if path.exists():
                artifacts[input_name] = path.read_text()
            else:
                artifacts[input_name] = f"[文件不存在: {input_name}]"

    return artifacts


if __name__ == "__main__":
    # 测试prompt构建
    import sys
    if len(sys.argv) >= 2:
        agent_name = sys.argv[1]
        prompt = build_agent_prompt(agent_name, {"project_name": "test", "current_state": "prd"})
        print(prompt[:500])
        print(f"\n... (总长度: {len(prompt)} 字符)")
