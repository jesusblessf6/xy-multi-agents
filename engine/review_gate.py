"""
评审门管理

负责：
1. 组织评审（汇总产出物，生成评审请求）
2. 记录评审结果
3. 根据结果决定流转方向
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional


WORKSPACE = Path("/Users/wing/myspace/code/xy-multi-agents")


def create_review_request(project_dir: Path, review_name: str, reviewers: list,
                          checklist: list, artifacts_summary: str) -> Path:
    """
    创建评审请求文档

    Args:
        project_dir: 项目目录
        review_name: 评审名称（如 prd_review）
        reviewers: 审核人列表
        checklist: 评审检查清单
        artifacts_summary: 产出物摘要

    Returns:
        评审文档路径
    """
    review_path = project_dir / "reviews" / f"{review_name}.md"

    content = f"""# {review_name} 评审请求

**生成时间**: {datetime.now().isoformat()}

## 审核人
{chr(10).join(f'- {r}' for r in reviewers)}

## 评审检查清单
{chr(10).join(f'- [ ] {item}' for item in checklist)}

## 产出物摘要
{artifacts_summary}

## 评审结果

- [ ] **Approved** - 通过，可进入下一阶段
- [ ] **Revision Needed** - 需要修改

### 审核意见
<!-- 请在此填写审核意见 -->

### 修改要求（如不通过）
<!-- 请在此列出具体修改要求 -->

---
*此文档由 XY Multi-Agents 系统自动生成*
"""

    review_path.write_text(content)
    return review_path


def parse_review_result(review_path: Path) -> dict:
    """
    解析评审文档，提取评审结果

    Returns:
        {"approved": bool, "comments": str, "revision_requests": list}
    """
    if not review_path.exists():
        return {"approved": False, "comments": "评审文档不存在", "revision_requests": []}

    content = review_path.read_text()

    # 简单解析：检查哪个checkbox被选中
    approved = "**Approved**" in content and "[x]" in content.split("**Approved**")[0].split("\n")[-1] if "**Approved**" in content else False
    revision_needed = "**Revision Needed**" in content and "[x]" in content.split("**Revision Needed**")[0].split("\n")[-1] if "**Revision Needed**" in content else False

    # 提取审核意见
    comments = ""
    if "### 审核意见" in content:
        parts = content.split("### 审核意见")
        if len(parts) > 1:
            comment_section = parts[1].split("###")[0].split("---")[0]
            comments = comment_section.strip()

    return {
        "approved": approved and not revision_needed,
        "comments": comments,
        "revision_requests": [],
    }


def save_review_record(project_dir: Path, review_name: str, result: dict):
    """保存评审记录到项目state"""
    state_file = project_dir / "state.json"
    with open(state_file) as f:
        state = json.load(f)

    state["reviews"][review_name] = {
        "status": "approved" if result["approved"] else "revision_needed",
        "comments": result["comments"],
        "timestamp": datetime.now().isoformat(),
    }

    with open(state_file, "w") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)
