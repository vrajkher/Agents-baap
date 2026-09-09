"""Local companion recorder for observable ChatGPT Desktop work.

This module does not hook private ChatGPT internals. It records only material the
user explicitly provides to the companion (prompt/response text) plus files in a
user-selected working folder.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import sqlite3
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


@dataclass
class DesktopArtifact:
    source_path: str
    snapshot_path: str
    sha256: str
    size: int
    captured_at: str


class ChatGPTDesktopRecorder:
    """Record visible ChatGPT Desktop work into a local SQLite audit log.

    Typical use:
    1. start_session(goal)
    2. record_prompt(copied_prompt)
    3. record_response(copied_visible_response)
    4. snapshot_working_files() for scripts/files ChatGPT created or edited
    5. record_correction(...) as the user iterates
    6. finish_session(...)

    The recorder deliberately avoids OS-wide clipboard/keylogging. The user must
    explicitly pass visible text or select a working directory to observe.
    """

    def __init__(
        self,
        db_path: str | Path = "data/chatgpt_desktop_work.db",
        artifact_root: str | Path = "data/chatgpt_desktop_artifacts",
    ) -> None:
        self.db_path = Path(db_path)
        self.artifact_root = Path(artifact_root)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.artifact_root.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self._create_schema()
        self.session_id: int | None = None

    def _create_schema(self) -> None:
        self.conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS desktop_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                goal TEXT NOT NULL,
                source TEXT NOT NULL DEFAULT 'chatgpt_desktop',
                started_at TEXT NOT NULL,
                finished_at TEXT,
                status TEXT,
                final_result TEXT,
                approved INTEGER NOT NULL DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS desktop_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                event_type TEXT NOT NULL,
                content TEXT,
                metadata_json TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL,
                FOREIGN KEY(session_id) REFERENCES desktop_sessions(id)
            );

            CREATE TABLE IF NOT EXISTS desktop_artifacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                source_path TEXT NOT NULL,
                snapshot_path TEXT NOT NULL,
                sha256 TEXT NOT NULL,
                size INTEGER NOT NULL,
                captured_at TEXT NOT NULL,
                FOREIGN KEY(session_id) REFERENCES desktop_sessions(id)
            );
            """
        )
        self.conn.commit()

    def start_session(self, goal: str) -> int:
        cur = self.conn.execute(
            "INSERT INTO desktop_sessions(goal, started_at) VALUES (?, ?)",
            (goal, _utc_now()),
        )
        self.conn.commit()
        self.session_id = int(cur.lastrowid)
        return self.session_id

    def _require_session(self) -> int:
        if self.session_id is None:
            raise RuntimeError("Start a desktop recording session first")
        return self.session_id

    def record_event(self, event_type: str, content: str = "", **metadata: object) -> None:
        session_id = self._require_session()
        self.conn.execute(
            """INSERT INTO desktop_events(session_id, event_type, content, metadata_json, created_at)
               VALUES (?, ?, ?, ?, ?)""",
            (session_id, event_type, content, json.dumps(metadata, ensure_ascii=False, default=str), _utc_now()),
        )
        self.conn.commit()

    def record_prompt(self, text: str) -> None:
        self.record_event("user_prompt", text)

    def record_response(self, text: str) -> None:
        self.record_event("chatgpt_visible_response", text)

    def record_correction(self, text: str) -> None:
        self.record_event("human_correction", text)

    def record_validation(self, name: str, passed: bool, details: str = "") -> None:
        self.record_event("validation", details, name=name, passed=passed)

    def record_script(self, code: str, language: str = "python", filename: str | None = None) -> None:
        self.record_event("generated_script", code, language=language, filename=filename)

    def snapshot_file(self, path: str | Path) -> DesktopArtifact:
        session_id = self._require_session()
        source = Path(path).expanduser().resolve()
        if not source.is_file():
            raise FileNotFoundError(source)

        digest = _sha256(source)
        session_dir = self.artifact_root / f"session_{session_id:06d}"
        session_dir.mkdir(parents=True, exist_ok=True)
        target = session_dir / f"{digest[:12]}_{source.name}"
        if not target.exists():
            shutil.copy2(source, target)

        artifact = DesktopArtifact(
            source_path=str(source),
            snapshot_path=str(target.resolve()),
            sha256=digest,
            size=source.stat().st_size,
            captured_at=_utc_now(),
        )
        self.conn.execute(
            """INSERT INTO desktop_artifacts(session_id, source_path, snapshot_path, sha256, size, captured_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (session_id, artifact.source_path, artifact.snapshot_path, artifact.sha256, artifact.size, artifact.captured_at),
        )
        self.conn.commit()
        return artifact

    def snapshot_working_files(
        self,
        folder: str | Path,
        patterns: Iterable[str] = ("*.py", "*.js", "*.ts", "*.json", "*.sql", "*.csv", "*.xlsx", "*.md"),
    ) -> list[DesktopArtifact]:
        root = Path(folder).expanduser().resolve()
        if not root.is_dir():
            raise NotADirectoryError(root)

        captured: list[DesktopArtifact] = []
        seen: set[Path] = set()
        for pattern in patterns:
            for path in root.rglob(pattern):
                if path.is_file() and path not in seen:
                    seen.add(path)
                    captured.append(self.snapshot_file(path))
        return captured

    def finish_session(self, final_result: str, approved: bool = False, status: str = "success") -> dict:
        session_id = self._require_session()
        self.conn.execute(
            """UPDATE desktop_sessions
               SET finished_at = ?, status = ?, final_result = ?, approved = ?
               WHERE id = ?""",
            (_utc_now(), status, final_result, int(approved), session_id),
        )
        self.conn.commit()
        return self.export_session(session_id)

    def export_session(self, session_id: int | None = None) -> dict:
        session_id = session_id or self._require_session()
        session = self.conn.execute(
            "SELECT * FROM desktop_sessions WHERE id = ?", (session_id,)
        ).fetchone()
        if session is None:
            raise KeyError(session_id)

        events = [dict(r) for r in self.conn.execute(
            "SELECT * FROM desktop_events WHERE session_id = ? ORDER BY id", (session_id,)
        )]
        artifacts = [dict(r) for r in self.conn.execute(
            "SELECT * FROM desktop_artifacts WHERE session_id = ? ORDER BY id", (session_id,)
        )]
        return {"session": dict(session), "events": events, "artifacts": artifacts}

    def close(self) -> None:
        self.conn.close()
