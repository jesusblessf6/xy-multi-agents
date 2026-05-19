---
name: test_review
description: 评审测试用例，从测试角度确认用例覆盖度和边界场景
allowed-tools: [file, search]
---

# 评审目标

从测试角度评审测试用例，确保用例覆盖度充分、边界场景完备。

# 评审输入

- `07_test/test_cases.md` — 测试用例文档

# 评审标准

- 功能测试是否覆盖所有需求
- 边界值和异常场景是否充分
- 用例优先级是否合理
- 预期结果是否明确
- 测试数据是否充分

# 严重等级定义

- **critical**: 用例严重缺失，无法保障质量
- **major**: 用例覆盖不完整，存在测试盲区
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
