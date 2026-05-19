---
name: test_review
description: 评审测试用例，从产品角度确认是否覆盖产品需求
allowed-tools: [file, search]
---

# 评审目标

从产品角度评审测试用例，确保用例覆盖了所有产品需求，验收场景完整。

# 评审输入

- `07_test/test_cases.md` — 测试用例文档
- `02_prd/prd.md` — PRD 文档（参考对照）

# 评审标准

- 测试用例是否覆盖所有用户故事
- 验收场景是否与 PRD 验收标准一致
- 业务流程是否完整覆盖
- 是否遗漏关键业务场景
- 用户视角的端到端场景是否充分

# 严重等级定义

- **critical**: 关键业务场景未覆盖
- **major**: 部分需求场景缺失
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
