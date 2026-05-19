"""Agent 执行器 — Prompt 组装 + 渐进式上下文注入 + delegate_task 请求对象"""

from pathlib import Path
from typing import Optional

from .agent_registry import get_skill, get_skill_summaries
from .config import AGENTS_DIR
from .types import AgentConfig, SkillSummary


def load_upstream_artifacts(project_dir: Path, agent_config: AgentConfig) -> dict[str, str]:
    """根据 Agent 的 inputs 配置，加载上游产出物内容

    路径由 agent_config.inputs + agent_config.output_dir 自动推导，
    不再硬编码路径映射。
    """
    artifacts: dict[str, str] = {}

    for input_name in agent_config.inputs:
        # 尝试在项目目录下搜索匹配的文件
        found = _find_artifact_file(project_dir, input_name)
        if found:
            artifacts[input_name] = found.read_text()
        else:
            artifacts[input_name] = f"[文件不存在: {input_name}]"

    return artifacts


def _find_artifact_file(project_dir: Path, input_name: str) -> Optional[Path]:
    """在项目目录下递归搜索匹配的产出物文件"""
    if not project_dir.exists():
        return None

    # 直接匹配项目根目录下的文件
    direct = project_dir / input_name
    if direct.exists():
        return direct

    # 在子目录中搜索
    for child in project_dir.iterdir():
        if child.is_dir() and not child.name.startswith("."):
            candidate = child / input_name
            if candidate.exists():
                return candidate

    return None


def build_agent_prompt(agent_config: AgentConfig, project_dir: Path,
                       project_name: str, current_state: str,
                       full_skills: bool = False) -> str:
    """构建 Agent 的完整执行 prompt

    Args:
        agent_config: Agent 配置
        project_dir: 项目工作区路径
        project_name: 项目名称
        current_state: 当前流水线状态
        full_skills: True=注入完整Skill内容，False=仅注入摘要(渐进式)
    """
    parts: list[str] = []

    # 1. 角色定义
    parts.append(f"# 你是: {agent_config.display_name}\n")
    parts.append(f"## 角色定义\n{agent_config.role}\n")

    # 2. 项目上下文
    parts.append("## 项目信息")
    parts.append(f"项目名: {project_name}")
    parts.append(f"当前阶段: {current_state}")
    parts.append(f"共享工作区: {project_dir}\n")

    # 3. 上游产出
    upstream = load_upstream_artifacts(project_dir, agent_config)
    if upstream:
        parts.append("## 上游产出（请仔细阅读）")
        for name, content in upstream.items():
            parts.append(f"### {name}\n{content}\n")

    # 4. Skills — 渐进式注入
    summaries = get_skill_summaries(agent_config.name)
    if summaries:
        if full_skills:
            # 全量注入（调试或特殊场景）
            parts.append("## 你的专业技能\n")
            for s in summaries:
                skill = get_skill(agent_config.name, s.name)
                parts.append(f"### {skill.name}\n{skill.description}\n\n{skill.content}\n")
        else:
            # 仅注入摘要，按需 read_skill 加载完整内容
            parts.append("## 你的可用技能 (Skills)")
            parts.append("以下是你绑定的技能摘要。如需查看详细步骤，请读取对应文件获取完整内容。\n")
            for s in summaries:
                tools_str = ", ".join(s.allowed_tools) if s.allowed_tools else "无限制"
                parts.append(f"- **{s.name}**: {s.description} (工具: {tools_str})")
                parts.append(f"  完整内容: `{s.file_path}`")
            parts.append("")

    # 5. RAG 知识 (暂不自动注入，Agent 按需读取)
    rag_dir = AGENTS_DIR / agent_config.name / "rag"
    if rag_dir.exists() and any(rag_dir.glob("*.md")):
        parts.append("## 领域知识库")
        parts.append(f"知识库目录: `{rag_dir}`")
        parts.append("请按需读取该目录下的文档获取领域知识。\n")

    # 6. 执行指令
    parts.append("## 执行指令")
    parts.append(agent_config.prompt_template)

    # 7. 产出要求
    parts.append("\n## 产出要求")
    parts.append(f"请将你的产出写入项目的 `{agent_config.output_dir}` 目录。")
    parts.append("确保文件内容完整、格式规范。完成后报告产出物清单。")

    return "\n".join(parts)


def build_delegate_request(agent_config: AgentConfig, project_dir: Path,
                           project_name: str, current_state: str) -> dict:
    """构建 Hermes delegate_task 请求对象

    Returns:
        {
            "goal": str,
            "context": str,
            "toolsets": list[str],
        }
    """
    context = build_agent_prompt(agent_config, project_dir, project_name, current_state)

    # 从 Skill 摘要中收集允许的工具
    summaries = get_skill_summaries(agent_config.name)
    toolsets: set[str] = set()
    for s in summaries:
        toolsets.update(s.allowed_tools)
    if not toolsets:
        toolsets = {"file", "terminal"}

    return {
        "goal": f"根据项目 {project_name} 的上下文，完成 {agent_config.display_name} 的职责，产出写入 {agent_config.output_dir}",
        "context": context,
        "toolsets": sorted(toolsets),
    }


def build_review_prompt(agent_config: AgentConfig, project_dir: Path,
                        project_name: str, gate_name: str,
                        review_input_path: str) -> str:
    """构建 Agent 评审的执行 prompt

    Agent 评审是一个独立动作：读取输入，应用评审 skill，产出结构化评审报告。
    评审标准、输出格式等由 skill 文件定义，不在代码中硬编码。
    """
    parts: list[str] = []

    # 1. 角色
    parts.append(f"# 你是: {agent_config.display_name}\n")
    parts.append(f"## 角色定义\n{agent_config.role}\n")

    # 2. 评审上下文
    parts.append("## 评审任务")
    parts.append(f"你正在参与评审门 **{gate_name}**。")
    parts.append(f"请根据你的专业领域，对以下输入进行评审。\n")

    # 3. 评审输入
    input_path = project_dir / review_input_path
    if input_path.exists():
        parts.append("## 评审输入")
        parts.append(input_path.read_text())
        parts.append("")
    else:
        parts.append(f"[警告: 评审输入文件不存在: {review_input_path}]\n")

    # 4. Skills — 评审 skill 应在其中
    summaries = get_skill_summaries(agent_config.name)
    if summaries:
        parts.append("## 你的可用技能 (Skills)")
        parts.append("以下是你绑定的技能摘要。请读取对应的评审技能文件获取完整的评审标准、输出格式和产出要求。\n")
        for s in summaries:
            tools_str = ", ".join(s.allowed_tools) if s.allowed_tools else "无限制"
            parts.append(f"- **{s.name}**: {s.description} (工具: {tools_str})")
            parts.append(f"  完整内容: `{s.file_path}`")
        parts.append("")

    # 5. RAG 知识
    rag_dir = AGENTS_DIR / agent_config.name / "rag"
    if rag_dir.exists() and any(rag_dir.glob("*.md")):
        parts.append("## 领域知识库")
        parts.append(f"知识库目录: `{rag_dir}`")
        parts.append("请按需读取该目录下的文档获取领域知识。\n")

    # 6. 执行指令
    parts.append("## 执行指令")
    parts.append(f"请读取你的评审技能文件，按照其中定义的评审标准、输出格式完成评审。")
    parts.append(f"将评审报告写入 `reviews/{gate_name}_{agent_config.name}.md`。")

    return "\n".join(parts)


def build_review_delegate_request(agent_config: AgentConfig, project_dir: Path,
                                  project_name: str, gate_name: str,
                                  review_input_path: str) -> dict:
    """构建评审用的 Hermes delegate_task 请求对象"""
    context = build_review_prompt(
        agent_config, project_dir, project_name, gate_name, review_input_path,
    )

    summaries = get_skill_summaries(agent_config.name)
    toolsets: set[str] = set()
    for s in summaries:
        toolsets.update(s.allowed_tools)
    if not toolsets:
        toolsets = {"file", "search"}

    return {
        "goal": f"参与评审门 {gate_name}，从{agent_config.display_name}角度评审 {review_input_path}",
        "context": context,
        "toolsets": sorted(toolsets),
    }
