"""Schema helpers for observable AI working records.

This module intentionally records only externally observable execution data.
It does not attempt to capture private chain-of-thought.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any
import uuid


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class Action:
    kind: str
    name: str
    input: dict[str, Any] = field(default_factory=dict)
    output: dict[str, Any] = field(default_factory=dict)
    status: str = "success"
    started_at: str = field(default_factory=utc_now)
    ended_at: str | None = None


@dataclass
class Decision:
    summary: str
    basis: str = ""
    confidence: float | None = None


@dataclass
class Validation:
    check: str
    passed: bool
    details: str = ""


@dataclass
class WorkRecord:
    goal: str
    model: str = "unknown"
    source: str = "chatgpt"
    run_id: str = field(default_factory=lambda: f"RUN-{uuid.uuid4().hex[:12]}")
    created_at: str = field(default_factory=utc_now)
    context: list[str] = field(default_factory=list)
    inputs: dict[str, Any] = field(default_factory=dict)
    output_requirements: list[str] = field(default_factory=list)
    actions: list[Action] = field(default_factory=list)
    decisions: list[Decision] = field(default_factory=list)
    rules: list[dict[str, Any]] = field(default_factory=list)
    validations: list[Validation] = field(default_factory=list)
    human_corrections: list[str] = field(default_factory=list)
    artifacts: list[str] = field(default_factory=list)
    final_result: dict[str, Any] = field(default_factory=dict)
    replay_instruction: str = ""
    skill_candidate: bool = False
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
