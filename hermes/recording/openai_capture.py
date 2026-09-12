"""Automatic capture of observable OpenAI Agents SDK work.

This module records traces/spans emitted by the OpenAI Agents SDK into a local
SQLite database. It captures externally observable execution data only: agent
runs, model generations, tool calls, handoffs, guardrails, custom spans, timing,
errors and exported span payloads. It does not and cannot capture private model
chain-of-thought.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any


class OpenAITraceStore:
    """Local exact ledger of OpenAI trace/span events."""

    def __init__(self, db_path: str | Path = "data/ai_work_records.db") -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS openai_traces (
                    trace_id TEXT PRIMARY KEY,
                    workflow_name TEXT,
                    started_at TEXT,
                    ended_at TEXT,
                    status TEXT NOT NULL DEFAULT 'running',
                    trace_json TEXT NOT NULL DEFAULT '{}'
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS openai_trace_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    trace_id TEXT NOT NULL,
                    span_id TEXT,
                    parent_id TEXT,
                    event_type TEXT NOT NULL,
                    span_type TEXT,
                    started_at TEXT,
                    ended_at TEXT,
                    error_json TEXT,
                    payload_json TEXT NOT NULL,
                    FOREIGN KEY(trace_id) REFERENCES openai_traces(trace_id)
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_openai_events_trace ON openai_trace_events(trace_id, id)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_openai_events_type ON openai_trace_events(span_type)"
            )

    def trace_start(self, trace: Any) -> None:
        exported = _safe_export(trace)
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO openai_traces
                (trace_id, workflow_name, started_at, ended_at, status, trace_json)
                VALUES (?, ?, ?, NULL, 'running', ?)
                """,
                (
                    getattr(trace, "trace_id", "unknown"),
                    getattr(trace, "name", ""),
                    _value(trace, "started_at"),
                    json.dumps(exported, ensure_ascii=False, default=str),
                ),
            )

    def trace_end(self, trace: Any) -> None:
        exported = _safe_export(trace)
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE openai_traces
                SET ended_at = ?, status = 'completed', trace_json = ?
                WHERE trace_id = ?
                """,
                (
                    _value(trace, "ended_at"),
                    json.dumps(exported, ensure_ascii=False, default=str),
                    getattr(trace, "trace_id", "unknown"),
                ),
            )

    def span_event(self, event_type: str, span: Any) -> None:
        span_data = getattr(span, "span_data", None)
        payload = _safe_export(span_data)
        span_type = getattr(span_data, "type", None)
        error = getattr(span, "error", None)
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO openai_trace_events
                (trace_id, span_id, parent_id, event_type, span_type,
                 started_at, ended_at, error_json, payload_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    getattr(span, "trace_id", "unknown"),
                    getattr(span, "span_id", None),
                    getattr(span, "parent_id", None),
                    event_type,
                    span_type,
                    _value(span, "started_at"),
                    _value(span, "ended_at"),
                    json.dumps(error, ensure_ascii=False, default=str) if error else None,
                    json.dumps(payload, ensure_ascii=False, default=str),
                ),
            )

    def get_trace(self, trace_id: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            trace = conn.execute(
                "SELECT * FROM openai_traces WHERE trace_id = ?", (trace_id,)
            ).fetchone()
            events = conn.execute(
                "SELECT * FROM openai_trace_events WHERE trace_id = ? ORDER BY id",
                (trace_id,),
            ).fetchall()
        if trace is None:
            return None
        return {
            "trace": dict(trace),
            "events": [dict(row) for row in events],
        }

    def latest_trace_id(self) -> str | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT trace_id FROM openai_traces ORDER BY rowid DESC LIMIT 1"
            ).fetchone()
        return row["trace_id"] if row else None

    def to_graphiti_episode(self, trace_id: str) -> dict[str, Any]:
        """Return a structured episode payload suitable for Graphiti ingestion."""
        record = self.get_trace(trace_id)
        if record is None:
            raise KeyError(f"Unknown trace_id: {trace_id}")

        useful_events: list[dict[str, Any]] = []
        for event in record["events"]:
            if event["event_type"] != "span_end":
                continue
            payload = json.loads(event["payload_json"] or "{}")
            useful_events.append(
                {
                    "span_type": event["span_type"],
                    "span_id": event["span_id"],
                    "parent_id": event["parent_id"],
                    "started_at": event["started_at"],
                    "ended_at": event["ended_at"],
                    "error": json.loads(event["error_json"]) if event["error_json"] else None,
                    "payload": payload,
                }
            )

        trace = record["trace"]
        return {
            "memory_type": "openai_agent_work_trace",
            "trace_id": trace_id,
            "workflow_name": trace["workflow_name"],
            "started_at": trace["started_at"],
            "ended_at": trace["ended_at"],
            "status": trace["status"],
            "observable_steps": useful_events,
            "privacy_note": "Observable execution only; no private chain-of-thought.",
        }


class _NoopProcessorBase:
    """Fallback type used only when openai-agents is not installed."""


def install_openai_agents_capture(
    db_path: str | Path = "data/ai_work_records.db",
) -> Any:
    """Install a tracing processor that automatically records every SDK trace/span.

    Requires the optional ``openai-agents`` package. The processor is added in
    addition to OpenAI's default tracing processor, so normal OpenAI tracing can
    continue while a local copy is also written to SQLite.
    """

    try:
        from agents.tracing import TracingProcessor, add_trace_processor
    except ImportError as exc:  # pragma: no cover - depends on optional package
        raise RuntimeError(
            "OpenAI Agents SDK is not installed. Run: pip install -e '.[openai]'"
        ) from exc

    store = OpenAITraceStore(db_path)

    class LocalWorkCaptureProcessor(TracingProcessor):
        def on_trace_start(self, trace: Any) -> None:
            store.trace_start(trace)

        def on_trace_end(self, trace: Any) -> None:
            store.trace_end(trace)

        def on_span_start(self, span: Any) -> None:
            store.span_event("span_start", span)

        def on_span_end(self, span: Any) -> None:
            store.span_event("span_end", span)

        def shutdown(self) -> None:
            return None

        def force_flush(self) -> None:
            return None

    processor = LocalWorkCaptureProcessor()
    add_trace_processor(processor)
    return processor


def _safe_export(obj: Any) -> dict[str, Any]:
    if obj is None:
        return {}
    export = getattr(obj, "export", None)
    if callable(export):
        try:
            value = export()
            return value if isinstance(value, dict) else {"value": value}
        except Exception as exc:  # recorder should never break the agent run
            return {"export_error": str(exc)}
    if isinstance(obj, dict):
        return obj
    return {"value": str(obj)}


def _value(obj: Any, name: str) -> str | None:
    value = getattr(obj, name, None)
    return str(value) if value is not None else None
