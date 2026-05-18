# XY Multi-Agents — 编码任务清单

> Claude Code 按此清单逐项编码。每项任务有明确的输入、输出和验收标准。
> 架构设计融合了 Pi-mono 的工作区与 SKILL 规范，以及 Hermes 的 delegate_task 最佳实践，并增设管理后台进行资产管控。

---

## 阶段规划

*   **Phase 1: 核心引擎与 CLI (T1 - T12)** - 构建底层状态流转、Hermes 调度与共享工作区通信机制。
*   **Phase 2: 管理后台 Backend API (T13 - T15)** - 提供用户权限、角色绑定及资产管控的 REST 接口。
*   **Phase 3: 管理后台 Web UI (T16 - T18)** - 提供可视化 Dashboard，支持 Web 端人工审批和 Skill 编辑。

---

### Phase 1: 核心引擎与 CLI (复用并升级现有设计)

> 注：T1-T12 的细节见原有规划，主要区别在于：需要实现对 `SKILL.md` (YAML Frontmatter) 的解析，并在 `agents/context.py` 和 `agents/executor.py` 中对接后台 API 获取配置，以及按 `docs/INTEGRATION.md` 使用 `delegate_task` 传递 context。

**关键更新任务卡点**:
- **T5 (agents/registry)**: 需要实现从 `SKILL.md` 解析 YAML Frontmatter 和正文，提取 `name`, `description`, `allowed-tools`。
- **T7 (agents/executor)**: 实现对 Hermes `delegate_task` 的调用，拼装动态的 `context`，并实现并行执行（如前端和后端任务）。
- **T9 (scheduler/orchestrator)**: 修改 `tick()` 逻辑，遇到 `review_gate` 暂停并生成后台可识别的 `awaiting_review` 状态。

---

### Phase 2: 管理后台 Backend API (FastAPI)

#### T13: 初始化 Backend 结构与数据库
**目标**: 创建 FastAPI 应用结构，配置 SQLite 数据库用于存储用户和权限。
**输入**: `docs/DESIGN.md` 第2节数据模型。
**输出**: 
- `backend/app/main.py`
- `backend/app/models/` (User, RoleBinding SQLAlchemy 模型)
- `backend/app/api/auth.py` (登录、JWT 签发)
**验收**: `uvicorn main:app` 启动成功，能通过 POST `/auth/login` 成功鉴权。

#### T14: Skill 与资产管理 API
**目标**: 提供接口，允许已鉴权用户查看和修改其绑定角色的 Agent 资产 (`SKILL.md`)。
**输入**: `docs/DESIGN.md` 第4.1节。
**输出**:
- `backend/app/api/assets.py`
**关键实现**:
- `GET /agents/{agent_name}/skills`: 扫描 `agents/{agent_name}/skills/` 目录返回 JSON 列表。
- `PUT /agents/{agent_name}/skills/{skill_name}`: 写入 Markdown 文件，校验 Frontmatter 格式。
- RBAC 校验：只有拥有 `product` 角色权限的用户，才能修改 `product` Agent 的技能。
**验收**: 使用 curl/Postman 成功创建并修改一个 `SKILL.md` 文件。

#### T15: 项目管控与审批 API
**目标**: 供 Web 端查询项目进度，执行人工评审的批准/驳回操作。
**输入**: `docs/DESIGN.md` 评审门流转设计。
**输出**:
- `backend/app/api/projects.py`
- `backend/app/api/reviews.py`
**关键实现**:
- `GET /projects`: 读取工作区 `projects/*/meta.json` 和 `state.json`。
- `POST /projects/{name}/reviews/{gate}/approve`: 修改 `state.json` 状态，以便后台的核心引擎 `tick()` 循环能继续流转。
**验收**: 接口能成功更新 `state.json` 的 review status。

---

### Phase 3: 管理后台 Frontend Web UI (Vue 3 / React)

#### T16: 初始化 Frontend 项目与 Dashboard
**目标**: 搭建前端框架，实现项目列表和进度展示。
**输出**:
- `frontend/src/views/Dashboard.vue` (或 .tsx)
- 登录页面与路由守卫。
**验收**: 登录后展示当前正在运行的项目进度树。

#### T17: 资产编辑器 (Skill Editor)
**目标**: 在线维护 Agent 的 `SKILL.md`。
**输出**:
- `frontend/src/views/AssetManager.vue`
**关键实现**:
- 左侧为 Agent 列表 (仅显示当前用户有权操作的)。
- 右侧为 Markdown 编辑器 (如 Monaco 或 Vditor)。
- 保存时调用 T14 接口写入文件系统。
**验收**: 在 Web 上修改 `SKILL.md` 后，核心引擎目录下对应文件被更新。

#### T18: 评审工作台 (Review Station)
**目标**: 处理 Pipeline 挂起的 `review_gate` 审批请求。
**输出**:
- `frontend/src/views/ReviewStation.vue`
**关键实现**:
- 查询当前 `awaiting_review` 的项目卡片。
- 展示上游产出文件 (如 `02_prd/prd.md`) 的内容预览。
- 提供【通过】和【驳回(并要求重做)】按钮。
- 调用 T15 接口提交审批结果。
**验收**: 点击【驳回】，输入“缺乏非功能需求”，成功阻断并让引擎回退状态。

---

## 执行指南 (给 Claude Code)

1. 先完成 Phase 1，确保底层机制在 CLI 下能通过 Mock 评审完成流转跑通。
2. 转入 Phase 2，搭建 FastAPI 桥梁。
3. 最后进行 Phase 3 前端界面的连通。
4. 在对接 `delegate_task` 时，务必严格参考 `INTEGRATION.md`。
