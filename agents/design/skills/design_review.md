---
name: design_review
description: 评审设计规格，从设计角度确认视觉一致性和设计规范合理性
allowed-tools: [file, search]
---

# 评审目标

从设计角度评审 UI/UX 设计规格，确保视觉一致性、设计规范合理、交互细节完善。

# 评审输入

- `03_design/design_spec.md` — 设计规格文档

# 评审标准

- 设计风格是否一致
- 交互流程是否符合用户习惯
- 信息层级是否清晰
- 是否考虑响应式适配
- 组件规范是否完整可复用

# 严重等级定义

- **critical**: 设计存在严重问题，无法指导前端开发
- **major**: 设计不完整，需要补充关键细节
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
