"""Pipeline YAML 加载器 — 验证 + 图结构导出"""

from functools import lru_cache
from pathlib import Path

import yaml

from .config import PIPELINE_CONFIG
from .types import PipelineDef, PipelineStateConfig


def load_pipeline(path: Path | None = None) -> PipelineDef:
    """加载并验证 pipeline.yaml"""
    config_path = path or PIPELINE_CONFIG
    with open(config_path) as f:
        raw = yaml.safe_load(f)
    return PipelineDef(**raw)


def get_state_config(state_name: str, pipeline: PipelineDef | None = None) -> PipelineStateConfig:
    """获取指定状态的配置"""
    if pipeline is None:
        pipeline = load_pipeline()
    return pipeline.states[state_name]


def get_graph_structure(pipeline: PipelineDef | None = None) -> dict:
    """导出图结构供前端渲染

    Returns:
        {
            "nodes": [{"id": "idle", "label": "项目刚创建", "type": "agent_execution"}, ...],
            "edges": [{"from": "idle", "to": "requirements", "label": ""}, ...]
        }
    """
    if pipeline is None:
        pipeline = load_pipeline()

    nodes = []
    edges = []

    for name, cfg in pipeline.states.items():
        nodes.append({
            "id": name,
            "label": cfg.description or name,
            "type": cfg.type,
            "agent": cfg.agent or cfg.agents,
        })

        # 正向边
        for target in cfg.next:
            edges.append({"from": name, "to": target, "label": ""})
        for target in cfg.next_approved:
            edges.append({"from": name, "to": target, "label": "通过"})
        for target in cfg.next_rejected:
            edges.append({"from": name, "to": target, "label": "驳回"})

    return {"nodes": nodes, "edges": edges}
