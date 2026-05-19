---
name: prd_review
description: 评审PRD文档，从架构角度评估技术可行性和实现复杂度
allowed-tools: [file, search]
---

# 评审目标

从架构角度评审 PRD 文档，评估技术可行性和实现复杂度。

# 评审输入

- `02_prd/prd.md` — 产品需求文档

# 评审标准

- 技术可行性是否充分
- 实现复杂度是否合理
- 是否存在技术实现风险
- 非功能需求是否在技术上可实现
- 是否需要调整需求以降低技术风险

# 严重等级定义

- **critical**: 技术上无法实现或需要重大架构调整
- **major**: 技术实现复杂度高，需要额外设计
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
