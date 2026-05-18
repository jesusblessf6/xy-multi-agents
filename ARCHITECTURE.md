# XY Multi-Agents 系统架构

## 1. 核心理念

**从需求到交付的全自动开发流水线**，由多个专职Agent协作完成软件开发全流程。每个Agent有明确职责边界，阶段成果需人工审核，PM Agent统筹全局。

设计原则（融合 Pi-mono & Hermes 最佳实践）：
- **职责单一与隔离**：每个Agent通过 Hermes `delegate_task` 在独立沙盒中运行。
- **评审必过**：关键节点设评审门，人工审核后才放行。
- **知识标准化 (Skill System)**：采用与 Pi-mono/Hermes 兼容的 `SKILL.md` 规范（YAML Frontmatter + Markdown）。
- **工作区共享 (Workspace Coordination)**：摒弃复杂的Agent间直接通信，采用共享文件系统（Shared Filesystem）作为状态与数据的唯一真相源。

## 2. 角色与 Agent 绑定体系 (RBAC)

系统提供一个**管理后台 (Management Portal)**。真人用户登录后，根据绑定的角色，维护对应Agent的大脑（Skills、RAG、Plugins）。

| 真实用户角色 | 绑定的 Agent | 维护职责范围 (在后台操作) | Agent 输出目录 |
|-------------|--------------|---------------------------|----------------|
| 售前/商务 | **presales** | 话术规范、客户调研模板、行业知识库 | `01_requirements/` |
| 项目经理 | **pm** | 敏捷流程规范、评审标准、进度计算插件 | (负责全局协调) |
| 产品经理 | **product** | PRD模板、竞品分析知识、原型规范 | `02_prd/` |
| UI/UX设计师 | **design** | 设计系统(Design System)、色彩体系、组件规范 | `03_design/` |
| 技术架构师 | **architect** | 技术选型标准、API规范模板、安全准则 | `04_architecture/` |
| 前端开发 | **frontend** | React/Vue最佳实践、前端Lint规则、构建脚本 | `05_frontend/` |
| 后端开发 | **backend** | 数据库规约、RESTful/RPC规范、架构样板 | `06_backend/` |
| 测试工程师 | **qa** | 测试用例模板、自动化测试脚本、边界值用例库 | `07_test/` |

## 3. 管理后台架构 (Management Backend)

管理后台独立于核心引擎，专门用于资产管理与人员映射。
- **User & Role DB**: 维护 `User -> Role -> Agent` 的映射。
- **Asset Manager**: 提供可视化界面编辑 `agents/<name>/skills/`, `rag/`, `plugins/`。
- **Project Dashboard**: PM和各角色可在此查看流水线状态、阻点，并进行**人工评审 (Review Gate)** 的批准/驳回操作。

## 4. 工作流 Pipeline

```text
[客户需求]
    │
    ▼
┌─────────┐
│ 售前     │ → requirements.md
└────┬────┘
     ▼
┌─────────┐
│ 产品     │ → prd.md + prototype.md
└────┬────┘
     ▼
╔═════════╗  ← PRD评审门 (产品经理+架构师在后台审核)
║ PRD评审 ║
╚────┬────╝
     ▼
... (后续设计、架构、开发、测试流程，均由PM Agent调度推进)
```

PM Agent 贯穿全程，负责：
- 轮询项目状态机 (State Machine)
- 检测上游产出就绪，通过 `delegate_task` 触发下游Agent
- 组织评审会（生成评审单，在后台Dashboard标记状态为待审）
- 跟踪整体进度，报告阻塞

## 5. Agent 知识资产 (Assets)

通过后台维护的资产，直接落盘到文件系统，供编排引擎运行时加载：

### 5.1 Skills (技能 - `agents/<name>/skills/`)
完全兼容 Hermes/Pi-mono 标准。
包含 YAML Frontmatter（定义名称、描述、允许的工具）和 Markdown 正文（触发条件、具体步骤、避坑指南）。

### 5.2 RAG (知识库 - `agents/<name>/rag/`)
存放公司内部的静态领域知识。支持 Markdown、PDF等，运行时按需向量检索或全量注入上下文。

### 5.3 Plugins (插件 - `agents/<name>/plugins/`)
Agent 专用的执行脚本或外部 API 集成（例如：QA Agent 的自动化测试执行脚本，前端 Agent 的脚手架生成器）。

## 6. 技术选型
- **底层引擎**: Python 3.12+, 基于文件系统的轻量状态机
- **Agent 执行**: Hermes `delegate_task`
- **后台服务**: FastAPI (REST API) + SQLite/PostgreSQL (仅存用户与角色，项目数据仍存文件系统)
- **前端后台**: Vue/React (提供Dashboard、评审界面、Skill编辑器)
