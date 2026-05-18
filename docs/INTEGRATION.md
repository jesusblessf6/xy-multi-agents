# XY Multi-Agents — Hermes 集成方案

> 核心思路：结合 Pi-mono 的**共享工作区机制**与 Hermes 的 **delegate_task 沙盒隔离机制**，实现流水线的自动流转。
> 管理后台 (Management System) 将动态下发配置给 PM Agent。

---

## 1. 架构定位

```text
┌─────────────────────────────────────────────────────────┐
│                 管理后台 Web UI (Dashboard)              │
│    (用户登录 -> 认领角色 -> 维护 Agent Skills -> 审批)   │
└───────────────────────────┬─────────────────────────────┘
                            │ (API / DB)
┌───────────────────────────▼─────────────────────────────┐
│                   核心引擎 (Engine)                     │
│  读取 projects/<name>/state.json + 扫描 agent.yaml       │
└───────────────────────────┬─────────────────────────────┘
                            │ (Tick Loop)
┌───────────────────────────▼─────────────────────────────┐
│                 PM Agent (Orchestrator)                 │
│  [调用 delegate_task]                                   │
│    ├── delegate_task(product)  ──→ 产品 Agent (独立沙盒) │
│    ├── delegate_task(architect)──→ 架构 Agent (独立沙盒) │
│    └── delegate_task(frontend) ──→ 前端 Agent (独立沙盒) │
└───────────────────────────┬─────────────────────────────┘
                            │ (File I/O)
┌───────────────────────────▼─────────────────────────────┐
│             共享工作区 projects/<project_name>/         │
│  02_prd/    04_architecture/    05_frontend/            │
└─────────────────────────────────────────────────────────┘
```

---

## 2. delegate_task 高级调用协议

Hermes 的 `delegate_task` 提供 `goal`, `context`, `toolsets` 等参数。我们通过引擎将后台维护的 Skill 动态组装进去。

### 2.1 Context 动态组装机制
从后台读取配置并组装 `context`（渐进式加载以省 Token）：

```python
# 示例：组装给产品 Agent 的调用
delegate_task(
    goal="根据需求文档 01_requirements/requirements.md 编写产品PRD，并输出到 02_prd/ 目录。",
    context="""
## 你的角色
{agent_role}

## 共享工作区
项目绝对路径: /Users/wing/myspace/code/xy-multi-agents/projects/online-shop/
请将所有的产出写入此目录下对应的子文件夹中。

## 上游产出摘要
[01_requirements/requirements.md] 已就绪。请自行使用 `file` 或 `terminal` tool 读取其完整内容。

## 你的可用技能 (Skills)
系统在后台为你绑定了以下技能，请严格遵循：
- {skill_1_name}: {skill_1_desc}
  (如需查看详细步骤，请读取 agents/product/skills/{skill_1_name}.md)

## 约束
- 你只能写入 02_prd/ 目录。
- 任务执行完毕后，必须返回简要的完成报告。
    """,
    toolsets=["file", "terminal"],  # 允许读写文件和使用命令行
    role="leaf",  # 作为叶子节点执行
)
```

### 2.2 并行执行 (Parallel Subagents)
在开发阶段（Development），前端和后端需要同时开工。此时使用 `delegate_task` 的 `tasks` 数组参数：

```python
delegate_task(
    tasks=[
        {
            "goal": "根据 04_architecture/ 目录下的架构和接口文档，开发前端代码。输出到 05_frontend/。",
            "context": "{frontend_assembled_context}",
            "toolsets": ["file", "terminal", "web"]
        },
        {
            "goal": "根据 04_architecture/ 目录下的接口规范，开发后端代码。输出到 06_backend/。",
            "context": "{backend_assembled_context}",
            "toolsets": ["file", "terminal", "web"]
        }
    ]
)
```
*   这将在 Hermes 内并发拉起两个子代理环境，两者互不干扰，但都操作同一个 `project` 工作区，并在完成后汇总结果给 PM Agent。

---

## 3. 协作与交互机制 (参考 Pi-mono / OpenClaw)

### 3.1 摒弃直接通信，采用文件通信
*   代理之间**不直接发消息**。
*   产品Agent生成 `prd.md` 后即销毁沙盒。
*   架构Agent启动时，通过读取工作区下的 `prd.md` 获取上游信息。
*   **异常回退**：如果架构Agent发现PRD有逻辑死循环无法实现，它不直接“质问”产品Agent，而是输出一个 `architecture_blocked_report.md`，并让 `delegate_task` 报错结束。PM Agent 捕获到错误后，解析该文件，流转状态退回 `prd` 阶段，并把该 report 作为 feedback 传入下一次对产品Agent的调用中。

### 3.2 进度与状态透出
1.  **Engine 观察者**: 独立于 PM Agent 的一个 Python 进程定期轮询 `projects/<name>/state.json`。
2.  **Web Dashboard**: 读取 `state.json`，在前端以甘特图或节点高亮的形式展示流水线流转。
3.  **评审打断**: 当 PM Agent 将状态推至 `review_gate` (如 `prd_review`) 时，暂停 `tick()` 循环。后台 Web 界面亮起红灯提示对应角色的用户。用户在页面上审阅 `02_prd/prd.md`，点击“通过/驳回”按钮。API 更新 `state.json`，PM Agent 的 `tick()` 循环继续执行。

---

## 4. PM Agent (Orchestrator) 的执行逻辑

在引入后台后，PM Agent 的行为更加明确：

```python
def orchestrator_tick(project):
    state = project.current_state
    stage_config = pipeline[state]
    
    # 1. 如果当前是人工评审门
    if stage_config.type == "review_gate":
        if project.reviews[state].status == "pending":
            # 挂起当前流程，通知后台用户
            notify_backend_users(stage_config.reviewers)
            project.update_review_status(state, "awaiting_review")
            return WAIT_FOR_REVIEW
            
        elif project.reviews[state].status == "approved":
            project.transition(stage_config.next_approved)
            return ADVANCE
            
        elif project.reviews[state].status == "rejected":
            # 携带后台填写的驳回意见，回退状态
            feedback = project.reviews[state].comments
            project.transition(stage_config.next_rejected, feedback=feedback)
            return RETREAT
            
    # 2. 如果当前是 Agent 执行节点
    elif stage_config.type == "agent_execution":
        agent_name = stage_config.agent
        
        # 通过 delegate_task 同步阻塞执行
        result_summary = delegate_task_to_hermes(agent_name, project)
        
        # 验证文件系统产出
        if verify_artifacts(project, agent_name):
            project.transition(stage_config.next)
            return ADVANCE
        else:
            project.record_error(f"{agent_name} 未完成规定的文件输出")
            return HALT
```
