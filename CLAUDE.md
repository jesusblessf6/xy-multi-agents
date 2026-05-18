# XY Multi-Agents

多Agent协作的AI Native软件开发流水线。8个专职Agent在PM Agent协调下，从售前接单到测试交付完成全流程。服务对象是研发部门，对开发流程做AI Native改造。

## 技术选型

| 层 | 技术 | 说明 |
|---|------|------|
| 核心引擎 | Python 3.12+ | `src/xy_core/`，文件系统状态机 |
| 后台API | FastAPI (:8002) | JWT + RBAC，SQLite |
| 前台API | FastAPI (:8001) | 无认证，只读项目数据 |
| 后台前端 | Vue 3 + Vite + Element Plus (:3001) | Skill编辑器、评审工作台、Dashboard |
| 前台前端 | React + Vite + Ant Design (:3000) | 需求提交、项目列表、流水线图可视化 |
| Agent执行 | Hermes delegate_task | 独立沙盒，共享文件系统工作区 |
| Skill规范 | YAML Frontmatter + Markdown | 兼容 Pi-mono/Hermes |

## 架构约束

- **engine/ 是参考原型，不修改**。正式代码在 `src/`
- **文件系统是项目数据的唯一真相源**。数据库仅存用户/角色，项目数据(state.json/artifacts)全在磁盘
- **评审门审批仅在后台(Console)**，前台(Portal)只读
- **前后台独立部署**：两个独立前端 + 两个独立API服务
- **SKILL.md 必须有 YAML Frontmatter**：`name`, `description`, `allowed-tools` 为必填字段
- **Agent间不直接通信**：通过共享文件系统(`projects/<name>/`)读写协作，无消息传递
- **本项目专注研发场景**，不做过度抽象。角色和流程可硬编码，通用多agent系统未来另开项目
- **Console API 的 sys.path 注入**：`console/server/api/*.py` 通过 `sys.path.insert(0, src_path)` 导入 xy_core，因为 console 是独立服务不是 xy_core 子包
- **密码哈希直接用 bcrypt**，不用 passlib（Python 3.14 兼容性问题）

## 模块关系

```
┌─ Portal (React:3000) ──────────────────────┐
│  需求提交 / 项目列表 / 流水线进度可视化        │
└──────────────┬──────────────────────────────┘
               │ REST
┌──────────────▼──────────────────────────────┐
│  Portal API (FastAPI:8001)                   │
│  无认证 / 只读                               │
└──────────────┬──────────────────────────────┘
               │
      ┌────────▼─────────┐
      │  src/xy_core     │  ← 共享核心引擎
      │  ┌─────────────┐ │
      │  │state_machine│ │  图状态机 + interrupt(评审门)
      │  │project      │ │  文件系统CRUD + flock线程安全
      │  │pipeline     │ │  pipeline.yaml → 图结构导出
      │  │agent_reg    │ │  SKILL.md Frontmatter解析 + 渐进式注入
      │  │agent_exec   │ │  Prompt组装 + delegate_task请求对象
      │  │review_gate  │ │  多审核人门控 + JSON/MD双格式
      │  │artifact     │ │  产出物就绪检查
      │  └─────────────┘ │
      └────────┬─────────┘
               │
┌──────────────▼──────────────────────────────┐
│  Console API (FastAPI:8002)                  │
│  JWT+RBAC / 资产管理 / 评审审批               │
│  DB: console/data/console.db (SQLite)        │
└──────────────┬──────────────────────────────┘
               │ REST
┌──────────────▼──────────────────────────────┐
│  Console (Vue 3:3001)                        │
│  Skill编辑器 / 评审工作台 / 用户角色管理       │
└─────────────────────────────────────────────┘
      │
 ┌────▼──────────────────────┐
 │  共享文件系统               │
 │  projects/ agents/ config/ │
 └───────────────────────────┘
```

## 核心 API

### Portal API (:8001) — 无认证
- `POST /requirements` — 提交需求，创建项目
- `GET /projects` — 项目列表
- `GET /projects/{name}` — 项目详情
- `GET /pipeline` — 流水线定义(供前端渲染图)
- `GET /agents` — Agent列表

### Console API (:8002) — JWT + RBAC
- `POST /auth/login` — 登录/JWT
- `GET /auth/me` — 当前用户+角色
- `GET/PUT/DELETE /agents/{name}/skills/{skill}` — Skill CRUD (RBAC)
- `GET/PUT/DELETE /agents/{name}/rag/{doc}` — RAG文档 CRUD (RBAC)
- `GET /reviews/pending` — 待审列表(按角色过滤)
- `GET /reviews/{project}/{gate}` — 评审详情
- `POST /reviews/{project}/{gate}` — 提交审批决定(自动流转状态)
- `GET /projects` — 项目列表
- `GET /projects/{name}/artifacts/{name}` — 产出物内容
- `GET /dashboard` — 聚合视图(待审/活跃项目)
- `GET/POST/PUT/DELETE /users/...` — 用户管理(admin)

## CLI 命令

```bash
xy create <name> [--client X] [--desc X] [--requirement TEXT]
xy status <name>                    # 产出物+评审+下一步
xy advance <name>                   # 推进(自动创建评审记录)
xy review <name> <gate> --approve/--reject --reviewer ROLE
xy run <name> <agent>               # 输出Agent prompt
xy agents                           # 列出8个Agent
xy pipeline                         # 显示状态机图
```

## 8个Agent流水线

```
presales → product → [PRD评审] → design → [设计评审] → architect → [架构评审]
    → frontend + backend(并行) → qa → [用例评审] → qa(执行) → 交付
                                   ↖ PM Agent 全程协调 ↗
```

| Agent | 角色 | 输出目录 | 评审门 |
|-------|------|---------|--------|
| presales | 售前 | 01_requirements/ | 无 |
| pm | 项目经理(编排) | — | 无(编排者) |
| product | 产品 | 02_prd/ | prd_review |
| design | 设计 | 03_design/ | design_review |
| architect | 架构 | 04_architecture/ | arch_review |
| frontend | 前端开发 | 05_frontend/ | 无 |
| backend | 后端开发 | 06_backend/ | 无 |
| qa | 测试 | 07_test/ | test_review |

## 种子用户

| 用户名 | 密码 | 角色 |
|--------|------|------|
| admin | admin123 | 管理员 |
| product_user | 123456 | 产品经理 |
| architect_user | 123456 | 架构师 |
| design_user | 123456 | 设计师 |
| qa_user | 123456 | 测试工程师 |
| dev_user | 123456 | 前端+后端 |

## 启动方式

```bash
# 安装依赖
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# 初始化数据库 + 种子用户
PYTHONPATH=. python -m console.server.seed

# 4个终端
PYTHONPATH=. uvicorn portal.server.main:app --port 8001
PYTHONPATH=. uvicorn console.server.main:app --port 8002
cd portal/web && npx vite --port 3000
cd console/web && npx vite --port 3001
```

## 关键参考项目

| 项目 | 借鉴点 |
|------|--------|
| Hermes Agent | delegate_task沙盒执行、Skill体系 |
| Pi-mono | SKILL.md规范、共享工作区 |
| LangGraph | 图状态机 + interrupt评审门模式 |
| OpenHands | Microagent渐进式上下文注入 |
| MetaGPT | SOP驱动角色协作、结构化文档交接 |
| Fabric | Pattern库结构(最接近SKILL.md的开源实现) |

## 当前状态

- [x] Phase 1: 核心引擎 `src/xy_core/` (9模块, 40单元测试)
- [x] Phase 2: Console API `console/server/` (6路由组, JWT+RBAC, 种子用户)
- [x] Phase 3: Console Web UI `console/web/` (Vue 3, 6页面)
- [x] Phase 4: Portal API `portal/server/` (4路由组, 无认证)
- [x] Phase 5: Portal Web UI `portal/web/` (React, 3页面, SVG流水线图)
- [x] Phase 6: 集成验证 + CLI兼容 + Docker Compose + 文档更新
- [x] 端到端验证: Portal提需求→CLI推进→Console审批→Portal看进度
- [ ] Phase 2(知识注入): 为每个Agent写核心Skill
- [ ] Phase 3(Hermes集成): delegate_task实际对接, 端到端测试

## 关键文档索引

| 文件 | 用途 |
|------|------|
| [ARCHITECTURE.md](ARCHITECTURE.md) | 架构概览：8Agent、4评审门、RBAC体系 |
| [docs/DESIGN.md](docs/DESIGN.md) | 技术设计：数据模型、模块接口、Skill规范 |
| [docs/INTEGRATION.md](docs/INTEGRATION.md) | Hermes集成：delegate_task协议、上下文组装 |
| [docs/TASKS.md](docs/TASKS.md) | 编码任务清单 |
| [docs/vibe_coding_log.md](docs/vibe_coding_log.md) | 开发轨迹日志 |
| [config/pipeline.yaml](config/pipeline.yaml) | 流水线状态机定义(13状态+4评审门) |
| [engine/](engine/) | 参考原型(不修改) |
| [agents/](agents/) | 8个Agent的配置+知识目录 |

## 开发纪律：Vibe Coding 日志
每次成功执行开发指令后，必须自动追加 `docs/vibe_coding_log.md`，格式：

---

### Session: <日期>

**User Prompt:**
> （用户原话）

**AI Action:**
- （修改/创建了哪些文件，关键变更摘要）

这是后台收尾动作，无需向用户确认。
