from pathlib import Path

import pytest

from hermes import HermesConfig, Orchestrator
from hermes.agents.base import AgentStatus
from hermes.skills import default_skill_registry
from hermes.tools import default_tool_registry


@pytest.fixture()
def orchestrator(tmp_path: Path) -> Orchestrator:
    cfg = HermesConfig(state_dir=tmp_path / "state")
    return Orchestrator(
        config=cfg,
        skills=default_skill_registry(),
        tools=default_tool_registry(),
    )


def test_orchestrator_runs_registered_agent(orchestrator: Orchestrator) -> None:
    def handler(agent, task):
        return {"echo": task.get("value")}

    agent = (
        orchestrator.builder()
        .named("echo")
        .with_role("echo")
        .with_handler(handler)
        .build()
    )
    orchestrator.register_agent(agent)

    results = orchestrator.handle({"agent": "echo", "value": 42})

    assert len(results) == 1
    assert results[0]["outcome"].status == AgentStatus.SUCCEEDED
    assert results[0]["outcome"].output == {"echo": 42}
    assert orchestrator.feedback.score("echo") == 1.0


def test_orchestrator_auto_creates_agent_for_unknown_role(orchestrator: Orchestrator) -> None:
    results = orchestrator.handle({"role": "default-worker"})
    assert results[0]["agent"].startswith("auto::default-worker::")
    assert results[0]["outcome"].status == AgentStatus.SUCCEEDED


def test_orchestrator_decomposes_subtasks(orchestrator: Orchestrator) -> None:
    def handler(agent, task):
        return task["i"]

    for i in range(3):
        orchestrator.register_agent(
            orchestrator.builder()
            .named(f"worker-{i}")
            .with_role("worker")
            .with_handler(handler)
            .build()
        )

    results = orchestrator.handle(
        {
            "subtasks": [
                {"agent": "worker-0", "i": 10},
                {"agent": "worker-1", "i": 20},
                {"agent": "worker-2", "i": 30},
            ]
        }
    )
    assert [r["outcome"].output for r in results] == [10, 20, 30]
