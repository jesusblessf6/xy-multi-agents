#!/usr/bin/env python3
"""
XY Multi-Agents CLI

命令行工具，用于管理项目和调度Agent。

Usage:
    xy create <project_name> [--client CLIENT] [--desc DESC]
    xy status <project_name>
    xy advance <project_name>
    xy review <project_name> <review_name> --approve/--reject [--comments COMMENTS]
    xy run <project_name> <agent_name>
    xy agents
    xy pipeline
"""

import argparse
import json
import sys
from pathlib import Path

# 将src目录加入path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from xy_core.agent_executor import build_agent_prompt, load_upstream_artifacts
from xy_core.agent_registry import list_agents, load_agent_config
from xy_core.artifact import check_artifacts_ready
from xy_core.config import AGENTS_DIR, WORKSPACE
from xy_core.pipeline import get_graph_structure, load_pipeline
from xy_core.project import Project
from xy_core.review_gate import ReviewGate
from xy_core.state_machine import StateMachine

import yaml


def cmd_create(args):
    """创建新项目"""
    try:
        if args.requirement:
            p = Project.create_with_requirement(
                args.project_name,
                requirement_text=args.requirement,
                client=args.client or "",
                description=args.desc or "",
                owner=args.owner or "",
            )
            print(f"项目已创建: {p.dir}")
            print(f"当前状态: requirements")
            print(f"需求已写入: {p.dir}/01_requirements/requirements.md")
        else:
            p = Project.create(
                args.project_name,
                client=args.client or "",
                description=args.desc or "",
                owner=args.owner or "",
            )
            print(f"项目已创建: {p.dir}")
            print(f"当前状态: idle")
            print(f"下一步: 提交客户需求到 {p.dir}/01_requirements/requirements.md")
    except FileExistsError as e:
        print(f"错误: {e}")


def cmd_status(args):
    """查看项目状态"""
    try:
        p = Project.load(args.project_name)
        sm = StateMachine()
        check = check_artifacts_ready(p, sm)

        print(f"项目: {p.meta.project_name}")
        print(f"客户: {p.meta.client}")
        print(f"当前阶段: {p.current_state}")
        print()
        print("产出物状态:")
        for name, info in p.state.artifacts.items():
            ready_mark = "✓" if p.check_artifact_ready(name) else "✗"
            print(f"  {ready_mark} {name}: {info.status}")

        print()
        print("评审状态:")
        for name, info in p.state.reviews.items():
            if isinstance(info, dict):
                print(f"  {name}: {info.get('status', 'pending')}")
            else:
                print(f"  {name}: {info}")

        # 下一步提示
        stage = sm.get_state_config(p.current_state)
        if stage.type == "review_gate":
            print(f"\n下一步: 等待评审 ({', '.join(sm.get_reviewers(p.current_state))})")
        elif stage.agent or stage.agents:
            agent_name = stage.agent or ", ".join(stage.agents)
            print(f"\n下一步: 执行 {agent_name} Agent")

        if check["ready"] and p.current_state != "idle":
            print("当前阶段产出已就绪，可以推进到下一阶段 (xy advance)")
        elif check["missing"]:
            print(f"待完成产出: {check['missing']}")

    except FileNotFoundError as e:
        print(f"错误: {e}")


def cmd_advance(args):
    """推进项目到下一阶段"""
    try:
        p = Project.load(args.project_name)
        sm = StateMachine()
        check = check_artifacts_ready(p, sm)

        if not check["ready"]:
            print(f"产出物未就绪: {check['missing']}")
            return

        next_state = sm.get_next_state(p.current_state, "artifacts_ready")
        if not next_state:
            print("已到达终态，无法推进")
            return

        p.transition_to(next_state)
        print(f"已推进到: {next_state}")

        # 如果进入评审门，自动创建评审记录
        if sm.is_interrupt_point(next_state):
            rg = ReviewGate(sm)
            rg.create_review(p.dir, p.meta.project_name, next_state)
            reviewers = sm.get_reviewers(next_state)
            print(f"评审门: {next_state}，等待审核: {', '.join(reviewers)}")

    except Exception as e:
        print(f"错误: {e}")


def cmd_review(args):
    """提交评审结果"""
    try:
        p = Project.load(args.project_name)
        sm = StateMachine()
        rg = ReviewGate(sm)

        reviewer_role = args.reviewer or ""
        if not reviewer_role:
            # 交互式选择审核人
            reviewers = sm.get_reviewers(args.review_name)
            if len(reviewers) == 1:
                reviewer_role = reviewers[0]
            else:
                print(f"请指定审核人角色 (--reviewer)，可选: {', '.join(reviewers)}")
                return

        record = rg.submit_decision(
            p.dir, args.review_name,
            reviewer_role=reviewer_role,
            approved=args.approve,
            comments=args.comments or "",
        )

        print(f"评审{'通过' if record.status == 'approved' else '已提交'}: {args.review_name}")

        # 如果评审已结束，自动流转状态
        if record.status == "approved":
            next_state = sm.get_next_state(args.review_name, "review_approved")
            if next_state:
                p.transition_to(next_state)
                print(f"已流转到: {next_state}")
        elif record.status == "rejected":
            next_state = sm.get_next_state(args.review_name, "review_rejected")
            if next_state:
                p.transition_to(next_state)
                print(f"已回退到: {next_state}")

    except Exception as e:
        print(f"错误: {e}")


def cmd_run(args):
    """运行指定Agent（输出构建的prompt）"""
    try:
        p = Project.load(args.project_name)
        agent_config = load_agent_config(args.agent_name)
        prompt = build_agent_prompt(
            agent_config,
            project_dir=p.dir,
            project_name=p.meta.project_name,
            current_state=p.current_state,
        )
        print(f"=== {args.agent_name} Agent Prompt ===")
        print(prompt)
        print(f"\n=== 总长度: {len(prompt)} 字符 ===")
        print("\n提示: 实际执行请通过 Hermes delegate_task 机制")
    except Exception as e:
        print(f"错误: {e}")


def cmd_agents(args):
    """列出所有Agent"""
    for agent_name in list_agents():
        config = load_agent_config(agent_name)
        skills_dir = AGENTS_DIR / agent_name / "skills"
        rag_dir = AGENTS_DIR / agent_name / "rag"
        skills_count = len(list(skills_dir.glob("*.md"))) if skills_dir.exists() else 0
        rag_count = len(list(rag_dir.glob("*.md"))) if rag_dir.exists() else 0
        print(f"  {config.name:12} {config.display_name:10} skills:{skills_count} rag:{rag_count}")


def cmd_pipeline(args):
    """显示pipeline定义"""
    pipeline = load_pipeline()
    graph = get_graph_structure(pipeline)

    print("Pipeline States:")
    for node in graph["nodes"]:
        marker = ""
        if node["type"] == "review_gate":
            marker = " [REVIEW GATE]"
        elif node["type"] == "parallel":
            marker = " [PARALLEL]"
        elif node["type"] == "terminal":
            marker = " [TERMINAL]"
        agent = node.get("agent", "")
        agent_str = f"agent: {agent}" if agent else ""
        print(f"  {node['id']:20} {agent_str}{marker}")

    print("\nTransitions:")
    for edge in graph["edges"]:
        label_str = f" ({edge['label']})" if edge["label"] else ""
        print(f"  {edge['from']:20} → {edge['to']}{label_str}")


def main():
    parser = argparse.ArgumentParser(prog="xy", description="XY Multi-Agents CLI")
    subparsers = parser.add_subparsers(dest="command")

    # create
    p_create = subparsers.add_parser("create", help="创建新项目")
    p_create.add_argument("project_name")
    p_create.add_argument("--client", default="")
    p_create.add_argument("--desc", default="")
    p_create.add_argument("--owner", default="")
    p_create.add_argument("--requirement", default="", help="直接写入需求文档内容")

    # status
    p_status = subparsers.add_parser("status", help="查看项目状态")
    p_status.add_argument("project_name")

    # advance
    p_advance = subparsers.add_parser("advance", help="推进到下一阶段")
    p_advance.add_argument("project_name")

    # review
    p_review = subparsers.add_parser("review", help="提交评审结果")
    p_review.add_argument("project_name")
    p_review.add_argument("review_name")
    p_review.add_argument("--approve", action="store_true")
    p_review.add_argument("--reject", action="store_true")
    p_review.add_argument("--comments", default="")
    p_review.add_argument("--reviewer", default="", help="审核人角色")

    # run
    p_run = subparsers.add_parser("run", help="运行Agent（输出prompt）")
    p_run.add_argument("project_name")
    p_run.add_argument("agent_name")

    # agents
    subparsers.add_parser("agents", help="列出所有Agent")

    # pipeline
    subparsers.add_parser("pipeline", help="显示pipeline定义")

    args = parser.parse_args()

    if args.command == "create":
        cmd_create(args)
    elif args.command == "status":
        cmd_status(args)
    elif args.command == "advance":
        cmd_advance(args)
    elif args.command == "review":
        args.approve = args.approve and not args.reject
        cmd_review(args)
    elif args.command == "run":
        cmd_run(args)
    elif args.command == "agents":
        cmd_agents(args)
    elif args.command == "pipeline":
        cmd_pipeline(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
