---
name: req_feasibility_review
description: 评估需求在客户预期成本下的技术可行性，识别技术风险和替代方案
allowed-tools: [file, search]
---

# 评审目标

从架构角度评估需求的技术可行性，重点关注客户预期成本下能否交付、技术风险和替代方案。

# 评审输入

- `01_requirements/requirements.md` — 售前 Agent 产出的结构化需求文档

# 评审标准

- 技术方案是否存在高风险项
- 是否有可行的替代方案降低成本
- 非功能需求（性能、安全、可用性）是否在成本内可实现
- 是否需要引入额外技术栈或依赖
- 现有技术资产是否可复用

# 严重等级定义

- **critical**: 技术上无法实现或成本远超预期的问题
- **major**: 需要显著调整技术方案的问题
- **minor**: 建议优化但不阻塞的问题

# 输出格式

请产出结构化的评审报告，包含以下部分：

1. **总评**: 一段话概述评审结论
2. **发现项**: 逐条列出问题，标注严重等级
3. **建议**: 针对每个发现项给出改进建议，含替代方案
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
