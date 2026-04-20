from __future__ import annotations

from typing import Any, Callable

from hermes.agents.base import Agent, AgentSpec
from hermes.memory.long_term import LongTermMemory
from hermes.skills.base import Skill


def _default_handler(agent: Agent, task: dict[str, Any]) -> dict[str, Any]:
    return {
        "agent": agent.spec.name,
        "role": agent.spec.role,
        "received": task,
        "status": "no-op handler; override via AgentBuilder.with_handler",
    }


class AgentBuilder:
    """Fluent builder that turns a task requirement into a ready-to-run Agent."""

    def __init__(
        self,
        skill_registry: dict[str, Skill],
        tool_registry: dict[str, Callable[..., Any]],
        long_term: LongTermMemory | None = None,
    ) -> None:
        self._skills = skill_registry
        self._tools = tool_registry
        self._long_term = long_term
        self._handler: Callable[[Agent, dict[str, Any]], Any] = _default_handler
        self._name: str | None = None
        self._role: str | None = None
        self._skill_names: list[str] = []
        self._tool_names: list[str] = []
        self._retry = 3
        self._mode = "ASYNC"

    def named(self, name: str) -> "AgentBuilder":
        self._name = name
        return self

    def with_role(self, role: str) -> "AgentBuilder":
        self._role = role
        return self

    def with_skills(self, *skills: str) -> "AgentBuilder":
        self._skill_names.extend(skills)
        return self

    def with_tools(self, *tools: str) -> "AgentBuilder":
        self._tool_names.extend(tools)
        return self

    def with_retry(self, retry: int) -> "AgentBuilder":
        self._retry = retry
        return self

    def with_mode(self, mode: str) -> "AgentBuilder":
        self._mode = mode
        return self

    def with_handler(
        self, handler: Callable[[Agent, dict[str, Any]], Any]
    ) -> "AgentBuilder":
        self._handler = handler
        return self

    def build(self) -> Agent:
        if not self._name or not self._role:
            raise ValueError("Agent requires both a name and a role")

        missing_skills = [s for s in self._skill_names if s not in self._skills]
        if missing_skills:
            raise KeyError(f"Unknown skills: {missing_skills}")
        missing_tools = [t for t in self._tool_names if t not in self._tools]
        if missing_tools:
            raise KeyError(f"Unknown tools: {missing_tools}")

        spec = AgentSpec(
            name=self._name,
            role=self._role,
            skills=list(self._skill_names),
            tools=list(self._tool_names),
            retry=self._retry,
            mode=self._mode,
        )
        return Agent(
            spec=spec,
            handler=self._handler,
            skill_registry={n: self._skills[n] for n in self._skill_names},
            tool_registry={n: self._tools[n] for n in self._tool_names},
            long_term=self._long_term,
        )
