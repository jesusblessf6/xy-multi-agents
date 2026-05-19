---
name: req_feasibility_review
description: 评估需求在客户预期成本下的可行性，从产品角度判断范围和优先级
allowed-tools: [file, search]
---

# 评审目标

从产品角度评估需求可行性，重点关注需求范围是否合理、交付优先级是否可行、MVP 边界是否清晰。

# 评审输入

- `01_requirements/requirements.md` — 售前 Agent 产出的结构化需求文档

# 评审标准

- 需求范围是否在客户预期成本内可实现
- 是否需要缩减范围或分阶段交付
- 交付时间线是否合理
- MVP 边界是否清晰
- 用户故事优先级是否合理

# 严重等级定义

- **critical**: 会导致项目无法在预期成本内交付的问题
- **major**: 会显著影响交付质量或时间的问题
- **minor**: 建议改进但不阻塞的问题

# 输出格式

请产出结构化的评审报告，包含以下部分：

1. **总评**: 一段话概述评审结论
2. **发现项**: 逐条列出问题，标注严重等级
3. **建议**: 针对每个发现项给出改进建议
4. **结论**: approve / reject / conditional_approve

# 产出要求

将评审报告写入 `reviews/{gate_name}_{role}.md`。

在报告末尾包含以下结构化块（供系统解析）：

```
<!-- review_result
verdict: approve|reject|conditional_approve
summary: 一句话总结
findings:
  - item: "问题描述"
    severity: critical|major|minor
    detail: "详细说明"
recommendations:
  - "改进建议"
conditions: []
-->
```
