# XY Multi-Agents 技术设计文档

> 核心设计思想融合了 Pi-mono 的标准 Skill 体系、共享工作区，以及 Hermes 的 delegate_task 机制。
> 增设管理后台（Management Backend）用于支持多角色协同与 Agent 资产管理。

---

## 1. 目录结构（含管理后台）

```text
xy-multi-agents/
├── docs/                       # 规划文档（Claude Code编码依据）
├── src/                        # 核心引擎代码 (Python)
│   ├── cli.py                  # CLI入口
│   ├── core/                   # 核心模块 (Project, StateMachine)
│   ├── agents/                 # Agent执行器 (Registry, Context, Executor)
│   ├── reviews/                # 评审门模块
│   └── scheduler/              # PM编排器
├── backend/                    # 管理后台 API 服务 (FastAPI)
│   ├── app/
│   │   ├── api/                # REST 接口 (Auth, Skills, Projects, Reviews)
│   │   ├── models/             # 数据库模型 (User, RoleBinding)
│   │   └── services/           # 调用 src/ 下的核心引擎代码
│   └── requirements.txt
├── frontend/                   # 管理后台 Web UI (Vue/React)
├── agents/                     # Agent资产目录 (通过后台修改)
│   ├── product/
│   │   ├── agent.yaml          # Agent基础配置
│   │   ├── skills/             # SKILL.md 集合 (遵循 Pi-mono 规范)
│   │   ├── rag/                # 知识库
│   │   └── plugins/            # 专属工具脚本
│   └── ... (共8个Agent)
├── projects/                   # 项目实例运行工作区 (Shared Workspace)
├── config/pipeline.yaml        # 流水线定义
└── pyproject.toml
```

---

## 2. 核心数据模型

### 2.1 后台系统数据库 (RDBMS: SQLite/Postgres)
后台数据库仅存储人员权限与系统元数据。**项目实际产出和代码仍以文件系统（projects/）为准**。

*   **User**: `id`, `username`, `password_hash`, `created_at`
*   **RoleBinding**: 
    *   `user_id` (FK)
    *   `role` (enum: presales, pm, product, design, architect, frontend, backend, qa)
    *   *说明*: 用户登录后，前端根据 RoleBinding 控制其可编辑哪几个 Agent 的 Skills/RAG，以及可审批哪些评审门。

### 2.2 项目状态 (projects/<name>/state.json)
记录流水线状态：
```json
{
  "project_name": "string",
  "current_state": "string",
  "artifacts": {
    "prd": {"status": "ready", "path": "02_prd/prd.md", "produced_by": "product"}
  },
  "reviews": {
    "prd_review": {"status": "awaiting_review", "reviewer_roles": ["product", "architect"]}
  }
}
```

---

## 3. Agent 资产规范 (参考 Pi-mono / Hermes)

### 3.1 Skill 规范 (`SKILL.md`)
每个 Skill 必须是一个独立的 Markdown 文件，顶部包含 YAML Frontmatter。编排引擎会自动解析。

```markdown
---
name: write-prd-standard
description: 编写标准的产品需求文档(PRD)的流程与模板
allowed-tools: [file, search]
---
# 触发条件
当上游售前需求文档(`requirements.md`)就绪，需要输出正式PRD时。

# 执行步骤
1. 阅读 `requirements.md`，提取核心功能点。
2. 按照以下模板生成 `prd.md`：
   ... (模板内容)
3. 检查边界条件，将疑点写入“待澄清问题”章节。

# 避坑指南
- 不要替架构师决定技术栈。
- 验收标准必须是可量化、可测试的。
```

### 3.2 Context 组装与注入机制 (Progressive Disclosure)
为避免超出 Token 限制，采用类似 Pi-mono 的**渐进式注入**：
1. **System Prompt**: 仅注入各 Skill 的 `name` 和 `description`。
2. **Runtime**: 如果 Agent 在执行中认为需要某个技能，可通过专门的内置 Tool (如 `read_skill`) 读取完整的 Markdown 内容，或在 `delegate_task` 的 `context` 组装阶段，由引擎直接把命中的高相关性 Skill 内容拼接进去。

---

## 4. 核心模块接口定义 (扩展)

### 4.1 backend/app/api — 后台接口层
管理后台提供以下 REST API，供 Web UI 调用：
*   `POST /auth/login`: 用户登录，返回 JWT。
*   `GET /users/me/roles`: 获取当前用户的 Role 列表。
*   `GET /agents/{agent_name}/skills`: 获取该 Agent 的技能列表 (读取文件系统)。
*   `PUT /agents/{agent_name}/skills/{skill_name}`: 更新技能内容 (限绑定的 Role 操作)。
*   `GET /projects`: 获取所有进行中的项目列表及进度。
*   `POST /projects/{name}/reviews/{gate}/approve`: 提交人工审批结果。

### 4.2 src/agents/registry.py — Agent 资产加载器
升级 `AgentRegistry` 以支持解析 YAML Frontmatter：
```python
class SkillDef:
    name: str
    description: str
    allowed_tools: list[str]
    content: str  # Markdown body

class AgentRegistry:
    def get_skills(self, agent_name: str) -> list[SkillDef]:
        """解析 agents/<name>/skills/*.md，分离 Frontmatter 和正文"""
```

### 4.3 src/scheduler/orchestrator.py — 编排器 (更新交互模式)
PM Agent 不再只通过 CLI 交互，而是与后台 API 联动：
*   到达 `review_gate` 时：将状态改为 `awaiting_review`，触发后台 WebSocket/Email 通知，然后在 Web UI 的 Dashboard 上高亮显示。
*   后台用户点击“通过”后：API 修改 `state.json` 的状态为 `approved`，编排器继续 `tick()` 向下流转。

---

## 5. 共享工作区 (Shared Workspace) 协作设计

所有子代理由 `delegate_task` 启动，工作目录统一设置在 `projects/<project_name>/` 下。
**无显式 Agent-to-Agent 通信协议**（借鉴 Pi-mono 的 Channel 隔离思想）：
1. 架构师生成 `04_architecture/api_spec.md`。
2. 后端 Agent 启动时，系统将其 Context 指向 `api_spec.md`，它读取后编写代码放入 `06_backend/`。
3. 如果后端发现 API 规范有矛盾，它将问题记录在 `06_backend/feedback.md`，状态标记为 `failed`。
4. PM Agent 检测到失败，读取 feedback，并重新调度架构师进行修复 (Retreat 机制)。