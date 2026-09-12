"""Capture observable ChatGPT Desktop work supplied by a local companion/observer.

This module intentionally records only user-visible/OS-visible events. It does not
attempt to access private model reasoning or hidden internal ChatGPT execution.
"""

from __future__ import annotations

import json
import sqlite3
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class DesktopEvent:
    event_type: str
    content: Any
    source: str = "chatgpt-desktop"
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)


class ChatGPTDesktopRecorder:
    """Persist observable ChatGPT Desktop events into SQLite.

    Typical event types: prompt, assistant_message, clipboard_text,
    created_file, modified_file, command, command_result, correction,
    validation, final_result.
    """

    def __init__(self, db_path: str = "data/chatgpt_desktop_work.db") -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS desktop_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    source TEXT NOT NULL,
                    content_json TEXT NOT NULL,
                    metadata_json TEXT NOT NULL,
                    created_at REAL NOT NULL
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_desktop_session ON desktop_events(session_id, id)"
            )

    def record(self, session_id: str, event_type: str, content: Any, **metadata: Any) -> int:
        event = DesktopEvent(event_type=event_type, content=content, metadata=metadata)
        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO desktop_events
                (session_id, event_type, source, content_json, metadata_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    session_id,
                    event.event_type,
                    event.source,
                    json.dumps(event.content, ensure_ascii=False, default=str),
                    json.dumps(event.metadata, ensure_ascii=False, default=str),
                    event.created_at,
                ),
            )
            return int(cursor.lastrowid)

    def record_prompt(self, session_id: str, text: str) -> int:
        return self.record(session_id, "prompt", text)

    def record_assistant_message(self, session_id: str, text: str) -> int:
        return self.record(session_id, "assistant_message", text)

    def record_correction(self, session_id: str, text: str) -> int:
        return self.record(session_id, "correction", text)

    def record_validation(self, session_id: str, name: str, passed: bool, evidence: Any = None) -> int:
        return self.record(
            session_id,
            "validation",
            {"name": name, "passed": passed, "evidence": evidence},
        )

    def record_final_result(self, session_id: str, result: Any) -> int:
        return self.record(session_id, "final_result", result)

    def get_session(self, session_id: str) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT id, event_type, source, content_json, metadata_json, created_at
                FROM desktop_events WHERE session_id = ? ORDER BY id
                """,
                (session_id,),
            ).fetchall()
        return [
            {
                "id": row[0],
                "session_id": session_id,
                "event_type": row[1],
                "source": row[2],
                "content": json.loads(row[3]),
                "metadata": json.loads(row[4]),
                "created_at": row[5],
            }
            for row in rows
        ]

    def export_session(self, session_id: str, output_path: str) -> str:
        events = self.get_session(session_id)
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(events, ensure_ascii=False, indent=2), encoding="utf-8")
        return str(path)
