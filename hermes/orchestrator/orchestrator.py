from __future__ import annotations

import logging
from typing import Any, Callable

from hermes.agents.base import Agent
from hermes.agents.builder import AgentBuilder
from hermes.communication.message_queue import MessageQueue
from hermes.core.config import HermesConfig
from hermes.errors.handler import ErrorHandler
from hermes.evolution.feedback import FeedbackLedger
from hermes.execution.engine import ExecutionEngine
from hermes.memory.long_term import LongTermMemory
from hermes.memory.short_term import ShortTermMemory
from hermes.skills.base import Skill

log = logging.getLogger("hermes.orchestrator")


class Orchestrator:
    """The Master Agent: decomposes tasks, assigns or spawns agents, monitors runs."""

    def __init__(
        self,
        config: HermesConfig | None = None,
        skills: dict[str, Skill] | None = None,
        tools: dict[str, Callable[..., Any]] | None = None,
    ) -> None:
        self.config = config or HermesConfig()
        self.skills: dict[str, Skill] = skills or {}
        self.tools: dict[str, Callable[..., Any]] = tools or {}
        self.agents: dict[str, Agent] = {}
        self.short_term = ShortTermMemory()
        self.long_term = LongTermMemory(self.config.ensure_state_dir() / "long_term.json")
        self.queue = MessageQueue()
        self.errors = ErrorHandler(max_retries=self.config.max_retries)
        self.engine = ExecutionEngine(error_handler=self.errors)
        self.feedback = FeedbackLedger(self.config.ensure_state_dir() / "feedback.json")

    # ------------------------------------------------------------------ registry
    def register_skill(self, skill: Skill) -> None:
        self.skills[skill.name] = skill

    def register_tool(self, name: str, tool: Callable[..., Any]) -> None:
        self.tools[name] = tool

    def register_agent(self, agent: Agent) -> None:
        self.agents[agent.spec.name] = agent

    # ------------------------------------------------------------------ builder
    def builder(self) -> AgentBuilder:
        return AgentBuilder(self.skills, self.tools, long_term=self.long_term)

    # ------------------------------------------------------------------ task flow
    def handle(self, task: dict[str, Any]) -> list[dict[str, Any]]:
        """Flow: receive -> decompose -> assign -> execute -> validate -> store."""
        self.short_term.push({"event": "task_received", "task": task})
        subtasks = self._decompose(task)
        results: list[dict[str, Any]] = []
        for subtask in subtasks:
            agent = self._select_or_create(subtask)
            outcome = self.engine.run(agent, subtask)
            self.feedback.record(agent.spec.name, subtask, outcome)
            results.append({"agent": agent.spec.name, "outcome": outcome})
        self.short_term.push({"event": "task_done", "task": task, "results": results})
        return results

    # ------------------------------------------------------------------ helpers
    def _decompose(self, task: dict[str, Any]) -> list[dict[str, Any]]:
        subtasks = task.get("subtasks")
        if isinstance(subtasks, list) and subtasks:
            return subtasks
        return [task]

    def _select_or_create(self, subtask: dict[str, Any]) -> Agent:
        target = subtask.get("agent")
        if target and target in self.agents:
            return self.agents[target]

        role = subtask.get("role", "generic-worker")
        name = subtask.get("agent") or f"auto::{role}::{len(self.agents)}"
        if name in self.agents:
            return self.agents[name]

        log.info("Creating agent '%s' for role '%s'", name, role)
        agent = (
            self.builder()
            .named(name)
            .with_role(role)
            .with_skills(*subtask.get("skills", []))
            .with_tools(*subtask.get("tools", []))
            .build()
        )
        self.register_agent(agent)
        return agent
