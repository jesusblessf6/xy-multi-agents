"""Pipeline API — 流水线图定义"""

import sys
from pathlib import Path

from fastapi import APIRouter

_src_path = str(Path(__file__).resolve().parents[4] / "src")
if _src_path not in sys.path:
    sys.path.insert(0, _src_path)

from xy_core.pipeline import load_pipeline, get_graph_structure

router = APIRouter()


@router.get("")
async def get_pipeline():
    """获取流水线图结构（供前端渲染节点和边）"""
    pipeline = load_pipeline()
    graph = get_graph_structure(pipeline)

    # 附带评审门定义
    review_gates = {}
    for name, gate in pipeline.review_gates.items():
        review_gates[name] = {
            "name": gate.name,
            "description": gate.description,
            "checklist": gate.checklist,
            "reviewers": [{"role": r.role, "focus": r.focus} for r in gate.reviewers],
        }

    return {
        "graph": graph,
        "review_gates": review_gates,
    }
