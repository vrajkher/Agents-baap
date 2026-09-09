"""Graphiti-backed relationship and experience memory for AI work records."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any


class GraphitiWorkMemory:
    """Store completed AI work records and OpenAI traces as Graphiti episodes.

    SQLite remains the exact local audit log. Graphiti is used for semantic,
    temporal and relationship memory across runs.
    """

    def __init__(
        self,
        uri: str | None = None,
        user: str | None = None,
        password: str | None = None,
    ) -> None:
        try:
            from graphiti_core import Graphiti
        except ImportError as exc:
            raise RuntimeError(
                "Graphiti is not installed. Run: pip install graphiti-core"
            ) from exc

        self.uri = uri or os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.user = user or os.getenv("NEO4J_USER", "neo4j")
        self.password = password or os.getenv("NEO4J_PASSWORD")
        if not self.password:
            raise ValueError("NEO4J_PASSWORD is required")
        self.graphiti = Graphiti(self.uri, self.user, self.password)

    async def initialize(self) -> None:
        """Create Graphiti indices and constraints once for the graph database."""
        await self.graphiti.build_indices_and_constraints()

    @staticmethod
    def _episode_payload(record: dict[str, Any]) -> dict[str, Any]:
        """Convert an observable work record into graph-friendly structured JSON."""
        return {
            "record_type": "ai_work_record",
            "run_id": record.get("run_id"),
            "goal": record.get("goal"),
            "source": record.get("source"),
            "model": record.get("model"),
            "context": record.get("context", []),
            "inputs": record.get("inputs", {}),
            "output_requirements": record.get("output_requirements", []),
            "actions": record.get("actions", []),
            "decisions": record.get("decisions", []),
            "rules": record.get("rules", []),
            "validations": record.get("validations", []),
            "human_corrections": record.get("human_corrections", []),
            "artifacts": record.get("artifacts", []),
            "final_result": record.get("final_result", {}),
            "replay_instruction": record.get("replay_instruction", ""),
            "skill_candidate": bool(record.get("skill_candidate")),
            "tags": record.get("tags", []),
        }

    async def _add_json_episode(
        self,
        *,
        name: str,
        payload: dict[str, Any],
        source_description: str,
        reference_time: datetime | None = None,
    ) -> None:
        from graphiti_core.nodes import EpisodeType

        reference_time = reference_time or datetime.now(timezone.utc)
        if reference_time.tzinfo is None:
            reference_time = reference_time.replace(tzinfo=timezone.utc)

        await self.graphiti.add_episode(
            name=name,
            episode_body=json.dumps(payload, ensure_ascii=False, default=str),
            source=EpisodeType.json,
            source_description=source_description,
            reference_time=reference_time,
        )

    async def add_work_record(self, record: dict[str, Any]) -> None:
        """Add one completed work record as a structured Graphiti episode."""
        created = record.get("created_at")
        try:
            reference_time = datetime.fromisoformat(created) if created else datetime.now(timezone.utc)
        except ValueError:
            reference_time = datetime.now(timezone.utc)

        payload = self._episode_payload(record)
        run_id = record.get("run_id", "unknown")
        goal = record.get("goal", "AI work record")
        await self._add_json_episode(
            name=f"AI Work Record {run_id}: {goal}",
            payload=payload,
            source_description="Observable AI working record from Hermes WorkRecorder",
            reference_time=reference_time,
        )

    async def add_openai_trace(self, trace_episode: dict[str, Any]) -> None:
        """Add a completed automatic OpenAI Agents SDK trace to Graphiti.

        The trace episode should come from ``OpenAITraceStore.to_graphiti_episode``.
        It contains observable spans such as model generations, tool calls,
        handoffs, guardrails, custom spans, errors and timing.
        """
        started = trace_episode.get("started_at")
        try:
            reference_time = datetime.fromisoformat(started) if started else datetime.now(timezone.utc)
        except (ValueError, TypeError):
            reference_time = datetime.now(timezone.utc)

        trace_id = trace_episode.get("trace_id", "unknown")
        workflow = trace_episode.get("workflow_name") or "OpenAI agent workflow"
        await self._add_json_episode(
            name=f"OpenAI Work Trace {trace_id}: {workflow}",
            payload=trace_episode,
            source_description="Observable OpenAI Agents SDK trace captured locally by Hermes",
            reference_time=reference_time,
        )

    async def search(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        """Search learned facts/relationships across prior work records."""
        results = await self.graphiti.search(query)
        output: list[dict[str, Any]] = []
        for item in results[:limit]:
            output.append(
                {
                    "uuid": getattr(item, "uuid", None),
                    "fact": getattr(item, "fact", str(item)),
                    "source_node_uuid": getattr(item, "source_node_uuid", None),
                    "target_node_uuid": getattr(item, "target_node_uuid", None),
                    "valid_at": str(getattr(item, "valid_at", "") or ""),
                    "invalid_at": str(getattr(item, "invalid_at", "") or ""),
                }
            )
        return output

    async def close(self) -> None:
        await self.graphiti.close()
