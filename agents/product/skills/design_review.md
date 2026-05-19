---
name: design_review
description: 评审设计规格，从产品角度确认是否符合产品意图和用户体验
allowed-tools: [file, search]
---

# 评审目标

从产品角度评审设计规格，确保设计符合产品意图、用户体验良好。

# 评审输入

- `03_design/design_spec.md` — 设计规格文档
- `02_prd/prd.md` — PRD 文档（参考对照）

# 评审标准

- 交互流程是否符合产品逻辑
- 信息展示是否满足用户需求
- 功能覆盖是否完整
- 用户体验是否流畅
- 边界场景是否考虑

# 严重等级定义

- **critical**: 设计与产品需求严重不符
- **major**: 设计遗漏关键功能或交互
- **minor**: 建议优化但不阻塞的问题

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
