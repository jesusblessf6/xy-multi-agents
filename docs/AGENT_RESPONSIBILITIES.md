# Agent 职责定义

> 本文档定义 8 个 Agent 的职责、产出物和评审门，作为系统审视和调整的基准。

## 流转全景

```
客户原始需求
  → presales: 结构化需求
  → [需求审核: presales(人审)] — 确认Agent理解正确
  → [需求可行性评审: product + architect(Agent评)] — 评估客户预期成本下能否实现
  → product: PRD + 原型
  → [PRD评审: product + architect]
  → design: 设计规格
  → [设计评审: design + product]
  → architect: 架构 + API规格
  → [架构评审: architect]
  → frontend + backend: 并行开发
  → qa: 测试用例
  → [用例评审: qa + product]
  → qa: 测试执行
  → 交付
```

### 审核与评审的区别

- **审核（人审）**：对应角色的人审核 Agent 产出，确认 Agent 理解正确、产出质量达标
- **评审（Agent 评）**：其他 Agent 对产出进行专业评审，评估可行性和合理性
- 两者串行：先人审通过，再 Agent 评审，避免人发现问题后 Agent 评审结果白费

---

## 1. 售前 Agent (presales)

**流水线位置**：需求入口，第一个执行的 Agent

**输入**：`00_raw_input/raw_requirement.md`（客户原始需求，通过 Portal 前端提交）

**职责**：
- 接收客户原始需求（可能是口语化的、不完整的）
- 将原始需求转化为结构化的 `requirements.md`
- 产出文档包含：项目背景、核心需求、功能需求、非功能需求、约束条件、待澄清问题
- 识别需求中的模糊点，列出待澄清问题供后续环节参考

**产出物**：`01_requirements/requirements.md`

**审核门**：需求审核 (req_audit) — 售前角色的人审核
- 确认 Agent 是否正确理解了客户需求
- 确认结构化是否准确，待澄清问题是否合理
- 驳回 → 回到 requirements 状态，Agent 重新处理

**评审门**：需求可行性评审 (req_feasibility) — 产品 + 架构 Agent 评审
- 产品 Agent：评估需求范围是否合理，交付优先级是否可行，MVP 边界是否清晰
- 架构 Agent：评估技术实现可行性，客户预期成本下能否交付，技术风险和替代方案
- 驳回 → 回到 requirements 状态，Agent 根据反馈修改

**当前状态**：skills/ 和 rag/ 为空，待知识注入

---

## 2. 产品 Agent (product)

**流水线位置**：需求通过 → PRD

**职责**：
- 基于售前 Agent 产出的结构化需求，编写完整的产品需求文档
- 编写原型描述文档（交互流程、页面布局描述）
- 定义用户故事、验收标准、优先级
- 补充非功能需求（性能、安全、可用性等）

**产出物**：`02_prd/prd.md` + `02_prd/prototype.md`

**评审门**：PRD 评审 — 产品 + 架构师 双审核
- 产品关注：需求完整性、用户故事合理性
- 架构师关注：技术可行性、实现复杂度

**当前状态**：skills/ 和 rag/ 为空，待知识注入

---

## 3. 设计 Agent (design)

**流水线位置**：PRD 通过 → 设计

**职责**：
- 基于 PRD 和原型描述，编写 UI/UX 设计规格
- 定义设计风格、组件规范、交互细节
- 描述信息层级、响应式适配方案
- 产出可指导前端开发的设计文档

**产出物**：`03_design/design_spec.md`

**评审门**：设计评审 — 设计 + 产品 双审核
- 设计关注：视觉一致性、设计规范合理性
- 产品关注：是否符合产品意图、用户体验

**当前状态**：skills/ 和 rag/ 为空，待知识注入

---

## 4. 架构师 Agent (architect)

**流水线位置**：设计通过 → 架构

**职责**：
- 基于需求和设计，设计系统整体架构
- 技术选型（框架、数据库、中间件等）
- 定义系统模块划分、依赖关系、部署架构
- 编写 API 规格文档（接口定义、数据模型、请求响应格式）
- 考虑性能、安全、扩展性

**产出物**：`04_architecture/architecture.md` + `04_architecture/api_spec.md`

**评审门**：架构评审 — 架构师 单审核
- 关注：架构合理性、技术选型、API 规范、性能安全、扩展性

**当前状态**：skills/ 和 rag/ 为空，待知识注入

---

## 5. 前端 Agent (frontend)

**流水线位置**：架构通过 → 开发（与后端**并行**）

**职责**：
- 基于设计规格 + 架构设计 + API 规格，实现前端代码
- 按照设计规范还原 UI 组件和交互
- 对接后端 API 接口
- 处理前端状态管理、路由、响应式布局

**产出物**：`05_frontend/` 目录下的前端代码

**评审门**：无（由 QA Agent 验证）

**当前状态**：skills/ 和 rag/ 为空，待知识注入

---

## 6. 后端 Agent (backend)

**流水线位置**：架构通过 → 开发（与前端**并行**）

**职责**：
- 基于架构设计 + API 规格，实现后端代码
- 实现业务逻辑、数据模型、API 端点
- 编写数据库脚本（建表、迁移）
- 处理认证授权、错误处理、日志

**产出物**：`06_backend/` 目录下的后端代码和数据库脚本

**评审门**：无（由 QA Agent 验证）

**当前状态**：skills/ 和 rag/ 为空，待知识注入

---

## 7. 测试 Agent (qa)

**流水线位置**：开发完成 → 测试（两个阶段）

**阶段一：编写测试用例**
- 基于需求 + 设计 + 架构，编写功能测试用例
- 覆盖正常流程、边界值、异常场景
- 定义用例优先级和预期结果
- 产出 `test_cases.md`

**阶段二：执行测试**（用例评审通过后）
- 按测试用例执行功能测试
- 记录测试结果、缺陷列表
- 产出测试报告 `test_report.md`

**产出物**：`07_test/test_cases.md` + `07_test/test_report.md`

**评审门**：用例评审 — QA + 产品 双审核（仅第一阶段）
- QA 关注：用例覆盖度、边界场景
- 产品关注：是否覆盖产品需求

**当前状态**：skills/ 和 rag/ 为空，待知识注入

---

## 8. 项目经理 Agent (pm)

**流水线位置**：全程协调，不处于流水线节点

**职责**：
- **编排调度**：决定何时触发哪个 Agent 执行
- **组织评审**：评审门到达时，通知对应审核人
- **进度跟踪**：监控各阶段状态，识别阻塞
- **异常处理**：评审驳回时协调返工、处理产出物缺失
- **上下文传递**：确保下游 Agent 能获取上游产出物

**产出物**：无独立产出物（编排者角色）

**评审门**：不直接参与评审

**当前状态**：skills/ 和 rag/ 为空，待知识注入

---

## 评审门汇总

| 评审门 | 类型 | 位置 | 审核人 | 驳回回退 |
|--------|------|------|--------|---------|
| 需求审核 (req_audit) | 人审 | requirements → req_feasibility | presales | → requirements |
| 需求可行性评审 (req_feasibility) | Agent评 | req_audit → prd | product + architect | → requirements |
| PRD 评审 (prd_review) | Agent评 | prd → design | product + architect | → prd |
| 设计评审 (design_review) | Agent评 | design → architecture | design + product | → design |
| 架构评审 (arch_review) | Agent评 | architect → development | architect | → architecture |
| 用例评审 (test_review) | Agent评 | test_case → test_execution | qa + product | → test_case |

## 已审视项

- [x] 售前 Agent 输入渠道：原始需求存入 00_raw_input/，Agent 读取后结构化
- [x] 售后审核与评审拆分：req_audit(人审) → req_feasibility(Agent评)，串行执行
- [x] 需求可行性评审：产品+架构评估客户预期成本下能否实现，非简单可行性
- [x] 评审门抽象：区分 human_audit(人审) 和 agent_review(Agent评)
- [x] 评审内容从 pipeline.yaml 迁移到 Agent skill 文件，pipeline 只管结构
- [x] Agent 评审作为独立动作：读取 skill → 产出结构化评审报告 → 系统解析 verdict

## 待审视项

- [ ] 各 Agent 职责边界是否清晰，有无遗漏或重叠
- [ ] 其他 Agent 产出是否也需要人审（如设计、架构）
- [ ] 前端/后端 Agent 无评审门，质量如何保证
- [ ] QA Agent 两个阶段的衔接是否顺畅
- [ ] rag/ 知识注入的优先级和内容规划
