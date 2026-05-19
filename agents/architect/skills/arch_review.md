---
name: arch_review
description: 评审系统架构设计，确认架构合理性、技术选型和扩展性
allowed-tools: [file, search]
---

# 评审目标

评审系统架构设计，确保架构合理、技术选型恰当、具备扩展性。

# 评审输入

- `04_architecture/architecture.md` — 架构设计文档
- `04_architecture/api_spec.md` — API 规格文档（可选参考）

# 评审标准

- 架构是否支撑业务需求
- 技术选型是否合理
- API 设计是否规范
- 是否考虑性能和安全
- 扩展性是否足够
- 模块划分是否合理

# 严重等级定义

- **critical**: 架构存在根本性问题，无法支撑业务
- **major**: 架构需要调整，影响模块设计
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
