from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable

from hermes.memory.short_term import ShortTermMemory
from hermes.memory.long_term import LongTermMemory
from hermes.skills.base import Skill


class AgentStatus(str, Enum):
    IDLE = "IDLE"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    RETIRED = "RETIRED"


@dataclass
class AgentSpec:
    name: str
    role: str
    skills: list[str] = field(default_factory=list)
    tools: list[str] = field(default_factory=list)
    retry: int = 3
    mode: str = "ASYNC"


@dataclass
class Agent:
    spec: AgentSpec
    handler: Callable[["Agent", dict[str, Any]], Any]
    skill_registry: dict[str, Skill] = field(default_factory=dict)
    tool_registry: dict[str, Callable[..., Any]] = field(default_factory=dict)
    short_term: ShortTermMemory = field(default_factory=ShortTermMemory)
    long_term: LongTermMemory | None = None
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    status: AgentStatus = AgentStatus.IDLE

    def use_skill(self, name: str, *args: Any, **kwargs: Any) -> Any:
        if name not in self.skill_registry:
            raise KeyError(f"Skill '{name}' not available to agent {self.spec.name}")
        return self.skill_registry[name].invoke(*args, **kwargs)

    def use_tool(self, name: str, *args: Any, **kwargs: Any) -> Any:
        if name not in self.tool_registry:
            raise KeyError(f"Tool '{name}' not available to agent {self.spec.name}")
        return self.tool_registry[name](*args, **kwargs)

    def run(self, task: dict[str, Any]) -> Any:
        self.status = AgentStatus.RUNNING
        self.short_term.push({"event": "task_started", "task": task})
        try:
            result = self.handler(self, task)
        except Exception as exc:
            self.status = AgentStatus.FAILED
            self.short_term.push({"event": "task_failed", "error": str(exc)})
            raise
        self.status = AgentStatus.SUCCEEDED
        self.short_term.push({"event": "task_completed", "result": result})
        if self.long_term is not None:
            self.long_term.store(
                key=f"{self.spec.name}:{task.get('id', 'anon')}",
                value={"task": task, "result": result},
            )
        return result
