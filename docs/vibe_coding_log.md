# Vibe Coding Log

> 本文件自动记录每次 AI 辅助开发的轨迹，作为项目演进的完整档案。

---

### Session: 2026-05-14

**User Prompt:**
> 我用hermes agent完善了该项目的框架设计，你过一下当前这个项目中的文件，了解一下整体的情况

**AI Action:**
- 阅读全项目文件，梳理项目概况（8Agent流水线、engine原型、CLI、规划文档）
- 输出项目整体情况总结：已完成部分和待实现部分

---

### Session: 2026-05-14

**User Prompt:**
> 当前我只是凭借我自己的经验推荐了 pi-mono 和 hermes agent 这两个项目作为参考。你可以根据项目的目的，看看是不是有更适合的开源项目作为参考，如果有的话跟我讨论一下吧。

**AI Action:**
- 调研 CrewAI、AutoGen、LangGraph、MetaGPT、ChatDev、OpenHands、SWE-agent、Fabric 等 15+ 开源项目
- 结论：Hermes+Pi-mono 继续作为主力参考（文件工作区协作和delegate_task是独特优势）
- 建议额外参考：LangGraph(状态机+interrupt)、OpenHands(渐进式上下文注入)、MetaGPT(SOP角色协作)

---

### Session: 2026-05-14

**User Prompt:**
> 在界面方面，我希望后台给对应角色的开发人员维护SOP、Skill等规范类的知识。前台是需求的管理，需求开发的进度展示。

**AI Action:**
- 确认前后台分工：前台(Portal)=需求+进度，后台(Console)=知识管理+审批
- 确认：前台用户为研发部门全员，评审门仅在后台，前后台独立部署
- 确认技术选型：前台React+后台Vue 3
- 完成前后台独立应用实现方案（6个Phase，43个任务）
- 创建 CLAUDE.md 项目快照
- 创建 vibe_coding_log.md

---

### Session: 2026-05-14

**User Prompt:**
> 我的远期目标是做一个通用的多agent协作系统，agent的角色不再是固定的，而是可以自定义的，协作的流程也可以自定义。也就是说在当前这个系统的基础上再抽象一层。如果结合这个远期目标，你觉得需要对当前项目架构做修改吗？

**AI Action:**
- 分析当前架构的硬编码程度（pipeline.yaml/agent.yaml骨架通用，但路径映射/RBAC/目录结构硬编码了研发场景）
- 提出两条路径：(A)先做通用系统再用它创建研发系统 (B)先做当前系统再另开项目做通用系统
- 分析了3处预防性调整（消灭路径映射硬编码、RBAC动态、agent列表动态）
- 用户决策：当前项目专注研发场景，不做预防性调整，通用系统未来另开项目
- 更新 CLAUDE.md 增加战略决策记录

---

### Session: 2026-05-14

**User Prompt:**
> 好的，那就按照我们的计划，开始开发吧！GO！

**AI Action:**
- 完成 Phase 1 核心引擎全部 11 个任务 (T1-T11)
- 创建 src/xy_core/ 包：config.py, types.py, pipeline.py, project.py, state_machine.py, agent_registry.py, agent_executor.py, review_gate.py, artifact.py, exceptions.py
- 更新 xy-cli.py 改用 xy_core（新增 --requirement 和 --reviewer 参数）
- 创建 pyproject.toml + venv + 依赖安装
- 修复 pipeline.yaml 兼容性（output_check 字符串/列表兼容）
- 修复 types.py 兼容性（review_gate dict/string, outputs string/dict）
- 修复 config.py WORKSPACE 路径推导
- 修复 agent_executor 目录不存在时的异常处理
- 40 个单元测试全部通过
- 清理 CLI 测试残留的临时项目

---

### Session: 2026-05-14

**User Prompt:**
> 好的继续

**AI Action:**
- 完成 Phase 2 Console API 全部 10 个任务 (T12-T21)
- 创建 console/server/ 骨架：FastAPI app factory、CORS、数据库初始化
- 实现 User + RoleBinding SQLAlchemy 模型
- 实现 auth API (登录/JWT/me)，改用 bcrypt 直接调用替代 passlib(兼容性问题)
- 实现 RBAC 守卫 (JWT认证 + 角色校验 + Agent资产权限隔离)
- 实现 assets API (Skills/RAG CRUD，RBAC: 角色匹配才可操作)
- 实现 reviews API (待审列表 + 提交审批 + 自动状态流转)
- 实现 projects API (列表 + 详情 + 产出物内容)
- 实现 dashboard API (聚合视图)
- 实现 users API (admin CRUD + 角色绑定)
- 创建种子脚本 (admin + 5个示例角色用户)
- RBAC 验证通过：产品经理只能编辑product Agent，操作architect返回403

---

### Session: 2026-05-14

**User Prompt:**
> 按顺序吧

**AI Action:**
- 完成 Phase 3 Console Web UI 全部 7 个任务 (T22-T28)
- 创建 Vue 3 + Vite + Pinia + Vue Router + Element Plus 项目
- 实现 Login 页面 (JWT存localStorage + 路由守卫)
- 实现 Layout 布局 (左侧导航 + 顶部用户信息 + 退出)
- 实现 Dashboard (待审数/活跃项目/待审列表卡片)
- 实现 ReviewStation (待审折叠面板 + 检查清单 + 通过/驳回按钮)
- 实现 AssetManager (Agent侧栏 + Skill/RAG Tab切换 + 新增/编辑/删除)
- 实现 SkillEditor (textarea编辑器 + YAML Frontmatter模板 + 格式校验)
- 实现 UserRoles (用户CRUD + 角色checkbox + admin权限)
- 配置 Vite proxy 转发 API 请求到 :8002
- 前后端联调验证通过：登录 → Dashboard → 评审 → 资产管理 → 用户管理

---

### Session: 2026-05-15

**User Prompt:**
> 继续

**AI Action:**
- 完成 Phase 4 Portal API 全部 5 个任务 (T29-T33)
- 创建 portal/server/ 骨架：FastAPI app factory, CORS
- 实现 requirements API (POST /requirements 提交需求+创建项目+写入requirements.md)
- 实现 projects API (GET /projects 列表, GET /projects/{name} 详情含artifacts/reviews)
- 实现 pipeline API (GET /pipeline 图结构+评审门定义)
- 实现 agents API (GET /agents 列表)
- 完成 Phase 5 Portal Web UI 全部 6 个任务 (T34-T39)
- 创建 React 18 + Vite + React Router + Ant Design 项目
- 实现 ProjectList (卡片列表+状态Tag+点击跳转)
- 实现 NewProject (表单提交需求+跳转详情)
- 实现 ProjectDetail (项目信息+产出物+评审状态+10秒轮询)
- 实现 PipelineGraph (SVG水平流水线图+当前状态高亮+评审门橙色)
- 配置 Vite proxy 转发 API 请求到 :8001

---

### Session: 2025-05-15

**User Prompt:**
> readme 中增加详细的部署方法

**AI Action:**
- 创建 `portal/web/Dockerfile` (Node.js 多阶段构建 + Nginx 托管 + API 反向代理)
- 创建 `console/web/Dockerfile` (同上)
- 更新 `Dockerfile.portal` 和 `Dockerfile.console` 改用 requirements.txt 安装依赖
- 修复 `console/server/requirements.txt`: passlib[bcrypt] → bcrypt>=4.0 (Python 3.14 兼容)
- 重写 README.md 部署章节：本地开发(5步)、Docker Compose(5步+常用命令)、生产部署(架构+步骤+Nginx示例+安全注意事项)

---

### Session: 2025-05-19

**User Prompt:**
> 售前agent的输入渠道是什么样的；售前agent输出的需求需要售前角色的人审核，另外需要让产品和架构进行评审，评估可行性（客户预期成本下能否实现）

**AI Action:**
- 修正售前Agent输入流程：`create_with_requirement()` 不再跳过Agent，原始需求存入 `00_raw_input/raw_requirement.md`，项目保持 `idle` 状态
- 新增两个评审门：`req_audit`(人审，presales角色) → `req_feasibility`(Agent评，product+architect)，串行执行
- 更新 `config/pipeline.yaml`：15个状态，6个评审门（+req_audit, req_feasibility）
- 更新 `agents/presales/agent.yaml`：inputs 指向 00_raw_input/，review_gate 改为两阶段
- 更新 `templates/project/state.json`：新增 raw_requirement artifact 和两个新评审门
- 创建 `templates/project/00_raw_input/` 目录
- 添加 `presales_user` 种子用户
- Console reviews API：评审通过后自动为下一个评审门创建记录
- CLI `cmd_advance`：idle 状态检查原始需求是否存在
- Portal API：提交需求后状态返回 idle
- 更新测试：44个测试全部通过
- 更新 `docs/AGENT_RESPONSIBILITIES.md`、`CLAUDE.md`、`README.md`

---

### Session: 2025-05-19 (2)

**User Prompt:**
> 流程设计尽量通用，减少硬编码，通过配置完成。审核和评审是Agent的两个动作，可以抽象出来。评审的具体内容通过skill/rag/sop配置，不要写死在代码里。

**AI Action:**
- `types.py`: PipelineStateConfig 新增 `gate_type`/`review_input`，ReviewGateDef 新增 `gate_type`/`review_input`，新增 `AgentReviewResult` 模型，ReviewerDecision 新增 `decision_type`/`review_result`
- `config/pipeline.yaml`: 所有 review_gate 状态加 gate_type (human_audit/agent_review)，agent_review 加 review_input，review_gates 段落去掉 checklist/focus (仅人审门 req_audit 保留 checklist)
- `state_machine.py`: interrupt_points 仅含 human_audit 门，新增 get_gate_type/is_human_audit/is_agent_review/get_review_input
- `review_gate.py`: 新增 submit_agent_review() 和 parse_agent_review_output()，更新 _generate_md 区分渲染人审和Agent评结果
- `agent_executor.py`: 新增 build_review_prompt() 和 build_review_delegate_request()
- 创建 9 个评审 skill 文件: product(3个), architect(3个), design(1个), qa(1个), product 有 3 个(含 design_review 和 test_review)
- 所有 agent.yaml 删除 review_gate 字段，pipeline.yaml 成为评审门唯一真相源
- Console reviews API: submit_review 拒绝 agent_review 门，新增 trigger-agent-review 端点，ReviewDetail 返回 gate_type
- Portal pipeline API: 返回 gate_type 字段
- 57 个测试全部通过（+13 新测试：gate_type、submit_agent_review、parse_agent_review_output、build_review_prompt、AgentReviewResult）

---
