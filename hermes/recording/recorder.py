"""SQLite-backed recorder for observable AI/agent work."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from .schema import Action, Decision, Validation, WorkRecord, utc_now


class WorkRecorder:
    def __init__(self, db_path: str | Path = "data/ai_work_records.db") -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
        self.current: WorkRecord | None = None

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS work_records (
                    run_id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    goal TEXT NOT NULL,
                    source TEXT NOT NULL,
                    model TEXT NOT NULL,
                    skill_candidate INTEGER NOT NULL DEFAULT 0,
                    status TEXT NOT NULL,
                    record_json TEXT NOT NULL
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_work_goal ON work_records(goal)"
            )

    def start(
        self,
        goal: str,
        *,
        model: str = "unknown",
        source: str = "chatgpt",
        inputs: dict[str, Any] | None = None,
        output_requirements: list[str] | None = None,
        context: list[str] | None = None,
        tags: list[str] | None = None,
    ) -> WorkRecord:
        self.current = WorkRecord(
            goal=goal,
            model=model,
            source=source,
            inputs=inputs or {},
            output_requirements=output_requirements or [],
            context=context or [],
            tags=tags or [],
        )
        return self.current

    def _require_current(self) -> WorkRecord:
        if self.current is None:
            raise RuntimeError("No active work record. Call start() first.")
        return self.current

    def action(
        self,
        kind: str,
        name: str,
        *,
        input: dict[str, Any] | None = None,
        output: dict[str, Any] | None = None,
        status: str = "success",
    ) -> None:
        rec = self._require_current()
        rec.actions.append(
            Action(
                kind=kind,
                name=name,
                input=input or {},
                output=output or {},
                status=status,
                ended_at=utc_now(),
            )
        )

    def decision(self, summary: str, basis: str = "", confidence: float | None = None) -> None:
        self._require_current().decisions.append(Decision(summary, basis, confidence))

    def rule(self, name: str, condition: str, action: str, **metadata: Any) -> None:
        self._require_current().rules.append(
            {"name": name, "condition": condition, "action": action, **metadata}
        )

    def validate(self, check: str, passed: bool, details: str = "") -> None:
        self._require_current().validations.append(Validation(check, passed, details))

    def correction(self, text: str) -> None:
        self._require_current().human_corrections.append(text)

    def artifact(self, path_or_uri: str) -> None:
        self._require_current().artifacts.append(path_or_uri)

    def finish(
        self,
        final_result: dict[str, Any],
        *,
        replay_instruction: str = "",
        skill_candidate: bool = False,
        status: str = "success",
    ) -> WorkRecord:
        rec = self._require_current()
        rec.final_result = final_result
        rec.replay_instruction = replay_instruction
        rec.skill_candidate = skill_candidate
        payload = json.dumps(rec.to_dict(), ensure_ascii=False, default=str)
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO work_records
                (run_id, created_at, goal, source, model, skill_candidate, status, record_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    rec.run_id,
                    rec.created_at,
                    rec.goal,
                    rec.source,
                    rec.model,
                    int(rec.skill_candidate),
                    status,
                    payload,
                ),
            )
        self.current = None
        return rec

    def get(self, run_id: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT record_json FROM work_records WHERE run_id = ?", (run_id,)
            ).fetchone()
        return json.loads(row["record_json"]) if row else None

    def search(self, text: str, limit: int = 20) -> list[dict[str, Any]]:
        pattern = f"%{text}%"
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT record_json FROM work_records
                WHERE goal LIKE ? OR record_json LIKE ?
                ORDER BY created_at DESC LIMIT ?
                """,
                (pattern, pattern, limit),
            ).fetchall()
        return [json.loads(row["record_json"]) for row in rows]
