---
name: prd_review
description: 评审PRD文档，从产品角度确认需求完整性和用户故事合理性
allowed-tools: [file, search]
---

# 评审目标

从产品角度评审 PRD 文档，确保需求完整、用户故事合理、验收标准明确。

# 评审输入

- `02_prd/prd.md` — 产品需求文档
- `02_prd/prototype.md` — 原型描述（可选参考）

# 评审标准

- 用户故事是否完整覆盖需求
- 验收标准是否明确可测
- 非功能需求是否充分
- 需求优先级是否合理
- 是否存在需求遗漏或矛盾

# 严重等级定义

- **critical**: 需求严重缺失或矛盾，无法指导开发
- **major**: 需求不完整，影响开发效率
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
