from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from hermes.agents.base import Agent, AgentStatus
from hermes.errors.handler import ErrorHandler


@dataclass
class ExecutionResult:
    agent: str
    status: AgentStatus
    output: Any
    attempts: int
    error: str | None = None


class ExecutionEngine:
    """Orchestrates agent runs with retries and post-hoc validation."""

    def __init__(
        self,
        error_handler: ErrorHandler | None = None,
        validator: Callable[[Agent, dict[str, Any], Any], bool] | None = None,
    ) -> None:
        self.error_handler = error_handler or ErrorHandler()
        self.validator = validator

    def run(self, agent: Agent, task: dict[str, Any]) -> ExecutionResult:
        attempts_before = len(self.error_handler.log)
        try:
            output = self.error_handler.run_with_retry(
                lambda: agent.run(task),
                agent_name=agent.spec.name,
            )
        except Exception as exc:
            attempts = len(self.error_handler.log) - attempts_before
            return ExecutionResult(
                agent=agent.spec.name,
                status=AgentStatus.FAILED,
                output=None,
                attempts=attempts,
                error=str(exc),
            )

        attempts = len(self.error_handler.log) - attempts_before + 1
        if self.validator is not None and not self.validator(agent, task, output):
            return ExecutionResult(
                agent=agent.spec.name,
                status=AgentStatus.FAILED,
                output=output,
                attempts=attempts,
                error="validation_failed",
            )
        return ExecutionResult(
            agent=agent.spec.name,
            status=agent.status,
            output=output,
            attempts=attempts,
        )
