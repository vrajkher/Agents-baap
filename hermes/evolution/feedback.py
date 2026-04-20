from __future__ import annotations

import json
import threading
import time
from pathlib import Path
from typing import Any

from hermes.execution.engine import ExecutionResult
from hermes.agents.base import AgentStatus


class FeedbackLedger:
    """Persists per-agent execution outcomes and produces simple performance scores.

    Feeds the SELF_EVOLUTION loop: agents with low scores can be reinforced,
    rebuilt with more skills, or retired.
    """

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self._lock = threading.Lock()
        self._data: dict[str, list[dict[str, Any]]] = {}
        if self.path.exists():
            self._data = json.loads(self.path.read_text(encoding="utf-8") or "{}")

    def record(self, agent_name: str, task: dict[str, Any], outcome: ExecutionResult) -> None:
        entry = {
            "timestamp": time.time(),
            "task": task,
            "status": outcome.status.value if isinstance(outcome.status, AgentStatus) else str(outcome.status),
            "attempts": outcome.attempts,
            "error": outcome.error,
        }
        with self._lock:
            self._data.setdefault(agent_name, []).append(entry)
            self._flush()

    def score(self, agent_name: str) -> float:
        history = self._data.get(agent_name, [])
        if not history:
            return 0.0
        successes = sum(1 for row in history if row.get("status") == AgentStatus.SUCCEEDED.value)
        return successes / len(history)

    def best_performing(self, top_n: int = 5) -> list[tuple[str, float]]:
        scores = [(agent, self.score(agent)) for agent in self._data]
        scores.sort(key=lambda item: item[1], reverse=True)
        return scores[:top_n]

    def _flush(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self._data, indent=2, default=str), encoding="utf-8")
