"""图状态机 — 借鉴 LangGraph interrupt 概念，纯 Python 实现"""

from typing import Optional

from .exceptions import InvalidStateTransition
from .pipeline import load_pipeline
from .types import PipelineDef, PipelineStateConfig, TransitionEvent


class StateMachine:
    """流水线状态机

    - 节点 = 状态 (agent_execution / review_gate / parallel / terminal)
    - 边 = 条件转换 (artifacts_ready / review_approved / review_rejected)
    - 评审门 = 中断点 (interrupt point)，仅 human_audit 门阻塞
    """

    def __init__(self, pipeline: PipelineDef | None = None):
        self._pipeline = pipeline or load_pipeline()
        # 仅 human_audit 门是中断点（阻塞等待人工操作）
        # agent_review 门不阻塞，系统自动派发
        self._interrupt_points: set[str] = {
            name for name, cfg in self._pipeline.states.items()
            if cfg.type == "review_gate" and (cfg.gate_type or "human_audit") == "human_audit"
        }

    @property
    def pipeline(self) -> PipelineDef:
        return self._pipeline

    def get_state_config(self, state_name: str) -> PipelineStateConfig:
        return self._pipeline.states[state_name]

    def get_next_state(self, current: str, event: str) -> Optional[str]:
        """根据当前状态和事件推导下一状态

        Events:
            - artifacts_ready: 产出物就绪，Agent执行完成
            - review_approved: 评审通过
            - review_rejected: 评审驳回
        """
        cfg = self.get_state_config(current)

        if cfg.type == "review_gate":
            if event == "review_approved":
                return cfg.next_approved[0] if cfg.next_approved else None
            elif event == "review_rejected":
                return cfg.next_rejected[0] if cfg.next_rejected else None
            else:
                raise InvalidStateTransition(
                    f"评审门 {current} 仅接受 review_approved/review_rejected 事件"
                )

        if cfg.type == "terminal":
            return None

        # agent_execution / parallel: 产出物就绪 → next
        if event == "artifacts_ready":
            return cfg.next[0] if cfg.next else None

        raise InvalidStateTransition(
            f"状态 {current} (type={cfg.type}) 不接受事件 {event}"
        )

    def is_interrupt_point(self, state: str) -> bool:
        """该状态是否为中断点（仅 human_audit 门）"""
        return state in self._interrupt_points

    def get_interrupt_points(self) -> list[str]:
        """所有中断点状态（human_audit 门）"""
        return sorted(self._interrupt_points)

    def get_gate_type(self, state: str) -> Optional[str]:
        """获取评审门类型: human_audit | agent_review | None"""
        cfg = self.get_state_config(state)
        if cfg.type == "review_gate":
            return cfg.gate_type or "human_audit"
        return None

    def is_human_audit(self, state: str) -> bool:
        return self.get_gate_type(state) == "human_audit"

    def is_agent_review(self, state: str) -> bool:
        return self.get_gate_type(state) == "agent_review"

    def get_parallel_agents(self, state: str) -> list[str]:
        """并行状态的Agent列表"""
        cfg = self.get_state_config(state)
        if cfg.type == "parallel" and cfg.agents:
            return cfg.agents
        return []

    def get_reviewers(self, state: str) -> list[str]:
        """评审门状态的审核人角色列表"""
        cfg = self.get_state_config(state)
        if cfg.type == "review_gate":
            return cfg.reviewers
        return []

    def get_review_input(self, state: str) -> Optional[str]:
        """获取Agent评审门的输入产出物路径"""
        cfg = self.get_state_config(state)
        if cfg.type == "review_gate":
            return cfg.review_input
        return None

    def get_output_check(self, state: str) -> list[str]:
        """该状态需要检查的产出物路径列表"""
        cfg = self.get_state_config(state)
        return cfg.output_check if cfg.output_check else []

    def get_rejected_target(self, state: str) -> Optional[str]:
        """评审驳回后回退到哪个状态"""
        cfg = self.get_state_config(state)
        if cfg.type == "review_gate" and cfg.next_rejected:
            return cfg.next_rejected[0]
        return None

    def is_terminal(self, state: str) -> bool:
        cfg = self.get_state_config(state)
        return cfg.type == "terminal"

    def all_states(self) -> list[str]:
        return list(self._pipeline.states.keys())
