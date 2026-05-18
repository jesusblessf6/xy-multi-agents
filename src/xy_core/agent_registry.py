"""Agent 注册表 — 配置加载 + SKILL.md Frontmatter 解析 + 渐进式注入"""

import re
from pathlib import Path

import yaml

from .config import AGENTS_DIR
from .exceptions import AgentConfigError, SkillFormatError
from .types import AgentConfig, RagDoc, SkillDef, SkillSummary


def load_agent_config(agent_name: str) -> AgentConfig:
    """加载 agent.yaml 配置"""
    config_path = AGENTS_DIR / agent_name / "agent.yaml"
    if not config_path.exists():
        raise AgentConfigError(f"Agent 配置不存在: {config_path}")
    with open(config_path) as f:
        raw = yaml.safe_load(f)
    return AgentConfig(**raw)


def list_agents() -> list[str]:
    """列出所有Agent（扫描 agents/ 目录）"""
    if not AGENTS_DIR.exists():
        return []
    return sorted(
        d.name for d in AGENTS_DIR.iterdir()
        if d.is_dir() and (d / "agent.yaml").exists()
    )


def _parse_frontmatter(content: str) -> tuple[dict, str]:
    """解析 YAML Frontmatter，返回 (metadata_dict, markdown_body)"""
    pattern = r"^---\s*\n(.*?)\n---\s*\n(.*)"
    match = re.match(pattern, content, re.DOTALL)
    if not match:
        return {}, content
    try:
        meta = yaml.safe_load(match.group(1)) or {}
    except yaml.YAMLError as e:
        raise SkillFormatError(f"Frontmatter YAML 解析失败: {e}")
    body = match.group(2).strip()
    return meta, body


def _render_frontmatter(meta: dict, body: str) -> str:
    """将 metadata 和 body 合成完整的 SKILL.md 内容"""
    frontmatter = yaml.dump(meta, allow_unicode=True, default_flow_style=False).strip()
    return f"---\n{frontmatter}\n---\n\n{body}\n"


def get_skills(agent_name: str) -> list[SkillDef]:
    """加载Agent的所有Skill，解析 Frontmatter"""
    skills_dir = AGENTS_DIR / agent_name / "skills"
    if not skills_dir.exists():
        return []

    skills = []
    for skill_file in sorted(skills_dir.glob("*.md")):
        content = skill_file.read_text()
        meta, body = _parse_frontmatter(content)
        skills.append(SkillDef(
            name=meta.get("name", skill_file.stem),
            description=meta.get("description", ""),
            allowed_tools=meta.get("allowed-tools", []),
            content=body,
        ))
    return skills


def get_skill_summaries(agent_name: str) -> list[SkillSummary]:
    """渐进式注入 — 仅返回摘要，不含完整正文"""
    skills_dir = AGENTS_DIR / agent_name / "skills"
    if not skills_dir.exists():
        return []

    summaries = []
    for skill_file in sorted(skills_dir.glob("*.md")):
        content = skill_file.read_text()
        meta, _ = _parse_frontmatter(content)
        summaries.append(SkillSummary(
            name=meta.get("name", skill_file.stem),
            description=meta.get("description", ""),
            allowed_tools=meta.get("allowed-tools", []),
            file_path=str(skill_file),
        ))
    return summaries


def get_skill(agent_name: str, skill_name: str) -> SkillDef:
    """加载单个 Skill"""
    skill_path = AGENTS_DIR / agent_name / "skills" / f"{skill_name}.md"
    if not skill_path.exists():
        raise SkillFormatError(f"Skill 不存在: {skill_path}")
    content = skill_path.read_text()
    meta, body = _parse_frontmatter(content)
    return SkillDef(
        name=meta.get("name", skill_name),
        description=meta.get("description", ""),
        allowed_tools=meta.get("allowed-tools", []),
        content=body,
    )


def save_skill(agent_name: str, skill_name: str, content: str) -> Path:
    """保存 SKILL.md 文件（Console 编辑器调用）"""
    skills_dir = AGENTS_DIR / agent_name / "skills"
    skills_dir.mkdir(parents=True, exist_ok=True)
    skill_path = skills_dir / f"{skill_name}.md"
    skill_path.write_text(content)
    return skill_path


def delete_skill(agent_name: str, skill_name: str) -> None:
    """删除 Skill"""
    skill_path = AGENTS_DIR / agent_name / "skills" / f"{skill_name}.md"
    if skill_path.exists():
        skill_path.unlink()


def validate_skill_frontmatter(content: str) -> tuple[bool, str]:
    """校验 SKILL.md Frontmatter 格式

    Returns:
        (valid, error_message)
    """
    try:
        meta, body = _parse_frontmatter(content)
    except SkillFormatError as e:
        return False, str(e)

    if not meta:
        return False, "缺少 YAML Frontmatter (需要 --- 分隔符)"

    required = ["name", "description"]
    for field in required:
        if field not in meta:
            return False, f"Frontmatter 缺少必填字段: {field}"

    if not body.strip():
        return False, "Skill 正文不能为空"

    return True, ""


def get_rag_docs(agent_name: str) -> list[RagDoc]:
    """列出Agent的RAG文档"""
    rag_dir = AGENTS_DIR / agent_name / "rag"
    if not rag_dir.exists():
        return []

    docs = []
    for doc_file in sorted(rag_dir.glob("*.md")):
        docs.append(RagDoc(
            name=doc_file.stem,
            file_path=str(doc_file),
            content="",
        ))
    return docs


def get_rag_content(agent_name: str, doc_name: str) -> str:
    """读取RAG文档内容"""
    doc_path = AGENTS_DIR / agent_name / "rag" / f"{doc_name}.md"
    if not doc_path.exists():
        raise AgentConfigError(f"RAG文档不存在: {doc_path}")
    return doc_path.read_text()


def save_rag_doc(agent_name: str, doc_name: str, content: str) -> Path:
    """保存RAG文档"""
    rag_dir = AGENTS_DIR / agent_name / "rag"
    rag_dir.mkdir(parents=True, exist_ok=True)
    doc_path = rag_dir / f"{doc_name}.md"
    doc_path.write_text(content)
    return doc_path


def delete_rag_doc(agent_name: str, doc_name: str) -> None:
    """删除RAG文档"""
    doc_path = AGENTS_DIR / agent_name / "rag" / f"{doc_name}.md"
    if doc_path.exists():
        doc_path.unlink()
