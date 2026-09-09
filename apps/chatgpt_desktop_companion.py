"""Simple Windows desktop companion for recording observable ChatGPT Desktop work.

Privacy boundary:
- No keylogging.
- No global clipboard monitoring.
- No hidden/private reasoning capture.
- Records only text the user explicitly pastes/types into the companion and file
  changes inside the user-selected working folder.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import sqlite3
import tkinter as tk
from datetime import datetime, timezone
from pathlib import Path
from tkinter import filedialog, messagebox, simpledialog, ttk


DB_PATH = Path("data/chatgpt_desktop_companion.db")
ARTIFACT_ROOT = Path("data/chatgpt_desktop_artifacts")
SKILL_ROOT = Path("generated_skills")


class DesktopCompanionStore:
    def __init__(self, db_path: Path = DB_PATH) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS runs (
                    run_id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    goal TEXT,
                    work_folder TEXT,
                    status TEXT NOT NULL,
                    approved INTEGER NOT NULL DEFAULT 0,
                    validation TEXT,
                    final_result TEXT
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    content TEXT,
                    metadata TEXT,
                    FOREIGN KEY(run_id) REFERENCES runs(run_id)
                )
                """
            )

    def create_run(self, goal: str, work_folder: str) -> str:
        run_id = datetime.now(timezone.utc).strftime("desktop_%Y%m%d_%H%M%S_%f")
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO runs(run_id, created_at, goal, work_folder, status) VALUES (?, ?, ?, ?, ?)",
                (run_id, datetime.now(timezone.utc).isoformat(), goal, work_folder, "recording"),
            )
        return run_id

    def event(self, run_id: str, event_type: str, content: str = "", metadata: dict | None = None) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO events(run_id, created_at, event_type, content, metadata) VALUES (?, ?, ?, ?, ?)",
                (
                    run_id,
                    datetime.now(timezone.utc).isoformat(),
                    event_type,
                    content,
                    json.dumps(metadata or {}, ensure_ascii=False),
                ),
            )

    def finish(self, run_id: str, validation: str, final_result: str, approved: bool) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "UPDATE runs SET status=?, approved=?, validation=?, final_result=? WHERE run_id=?",
                ("approved" if approved else "finished", int(approved), validation, final_result, run_id),
            )

    def export_run(self, run_id: str) -> dict:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            run = conn.execute("SELECT * FROM runs WHERE run_id=?", (run_id,)).fetchone()
            events = conn.execute("SELECT * FROM events WHERE run_id=? ORDER BY id", (run_id,)).fetchall()
        return {
            "run": dict(run) if run else {},
            "events": [dict(row) for row in events],
        }


class FolderSnapshot:
    def __init__(self, folder: Path) -> None:
        self.folder = folder

    @staticmethod
    def _hash_file(path: Path) -> str:
        h = hashlib.sha256()
        with path.open("rb") as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b""):
                h.update(chunk)
        return h.hexdigest()

    def capture(self) -> dict[str, dict]:
        result: dict[str, dict] = {}
        if not self.folder.exists():
            return result
        for path in self.folder.rglob("*"):
            if not path.is_file():
                continue
            try:
                stat = path.stat()
                rel = str(path.relative_to(self.folder))
                result[rel] = {
                    "size": stat.st_size,
                    "mtime": stat.st_mtime,
                    "sha256": self._hash_file(path),
                }
            except (OSError, PermissionError):
                continue
        return result

    @staticmethod
    def diff(before: dict[str, dict], after: dict[str, dict]) -> dict[str, list[str]]:
        before_keys = set(before)
        after_keys = set(after)
        created = sorted(after_keys - before_keys)
        deleted = sorted(before_keys - after_keys)
        modified = sorted(
            key for key in before_keys & after_keys
            if before[key].get("sha256") != after[key].get("sha256")
        )
        return {"created": created, "modified": modified, "deleted": deleted}


class ChatGPTDesktopCompanion(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("ChatGPT Desktop Work Recorder")
        self.geometry("980x720")
        self.minsize(860, 620)

        self.store = DesktopCompanionStore()
        self.run_id: str | None = None
        self.work_folder: Path | None = None
        self.folder_snapshot_before: dict[str, dict] = {}

        self.goal_var = tk.StringVar()
        self.folder_var = tk.StringVar()
        self.validation_var = tk.StringVar()
        self.status_var = tk.StringVar(value="Ready")

        self._build_ui()

    def _build_ui(self) -> None:
        main = ttk.Frame(self, padding=12)
        main.pack(fill="both", expand=True)

        top = ttk.LabelFrame(main, text="1. Start Work", padding=10)
        top.pack(fill="x")
        ttk.Label(top, text="Goal").grid(row=0, column=0, sticky="w")
        ttk.Entry(top, textvariable=self.goal_var).grid(row=0, column=1, sticky="ew", padx=8)
        ttk.Button(top, text="Select Work Folder", command=self.select_folder).grid(row=1, column=0, pady=8, sticky="w")
        ttk.Entry(top, textvariable=self.folder_var, state="readonly").grid(row=1, column=1, sticky="ew", padx=8)
        ttk.Button(top, text="Start Recording", command=self.start_recording).grid(row=0, column=2, rowspan=2, padx=8)
        top.columnconfigure(1, weight=1)

        capture = ttk.LabelFrame(main, text="2. Capture Visible ChatGPT Work", padding=10)
        capture.pack(fill="both", expand=True, pady=(10, 0))

        ttk.Label(capture, text="Your Prompt / Instruction").grid(row=0, column=0, sticky="w")
        self.prompt_text = tk.Text(capture, height=6, wrap="word")
        self.prompt_text.grid(row=1, column=0, sticky="nsew", padx=(0, 6))
        ttk.Label(capture, text="ChatGPT Visible Answer / Code / Script").grid(row=0, column=1, sticky="w")
        self.answer_text = tk.Text(capture, height=6, wrap="word")
        self.answer_text.grid(row=1, column=1, sticky="nsew", padx=(6, 0))
        ttk.Button(capture, text="Capture Prompt + Answer", command=self.capture_chat).grid(row=2, column=0, columnspan=2, pady=8)
        capture.columnconfigure(0, weight=1)
        capture.columnconfigure(1, weight=1)
        capture.rowconfigure(1, weight=1)

        actions = ttk.LabelFrame(main, text="3. Record Result", padding=10)
        actions.pack(fill="x", pady=(10, 0))
        ttk.Button(actions, text="Scan Changed Files", command=self.scan_files).grid(row=0, column=0, padx=4)
        ttk.Button(actions, text="Record Correction", command=self.record_correction).grid(row=0, column=1, padx=4)
        ttk.Label(actions, text="Validation").grid(row=0, column=2, padx=(16, 4))
        ttk.Entry(actions, textvariable=self.validation_var, width=34).grid(row=0, column=3, sticky="ew")
        ttk.Button(actions, text="Finish", command=lambda: self.finish(False)).grid(row=0, column=4, padx=4)
        ttk.Button(actions, text="Approve", command=lambda: self.finish(True)).grid(row=0, column=5, padx=4)
        ttk.Button(actions, text="Freeze as Skill", command=self.freeze_skill).grid(row=0, column=6, padx=4)
        actions.columnconfigure(3, weight=1)

        logbox = ttk.LabelFrame(main, text="Recorder Log", padding=8)
        logbox.pack(fill="both", expand=True, pady=(10, 0))
        self.log_text = tk.Text(logbox, height=10, state="disabled", wrap="word")
        self.log_text.pack(fill="both", expand=True)

        ttk.Label(main, textvariable=self.status_var, anchor="w").pack(fill="x", pady=(8, 0))

    def _log(self, text: str) -> None:
        self.log_text.configure(state="normal")
        self.log_text.insert("end", f"{datetime.now().strftime('%H:%M:%S')}  {text}\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")
        self.status_var.set(text)

    def _require_run(self) -> bool:
        if not self.run_id:
            messagebox.showwarning("Recorder", "Start Recording first.")
            return False
        return True

    def select_folder(self) -> None:
        selected = filedialog.askdirectory(title="Select folder ChatGPT is working in")
        if selected:
            self.work_folder = Path(selected)
            self.folder_var.set(selected)
            self._log(f"Work folder selected: {selected}")

    def start_recording(self) -> None:
        goal = self.goal_var.get().strip()
        if not goal:
            messagebox.showwarning("Recorder", "Enter the work goal first.")
            return
        folder = str(self.work_folder or "")
        self.run_id = self.store.create_run(goal, folder)
        self.folder_snapshot_before = FolderSnapshot(self.work_folder).capture() if self.work_folder else {}
        self._log(f"Recording started: {self.run_id}")

    def capture_chat(self) -> None:
        if not self._require_run():
            return
        prompt = self.prompt_text.get("1.0", "end").strip()
        answer = self.answer_text.get("1.0", "end").strip()
        if prompt:
            self.store.event(self.run_id, "user_prompt", prompt)
        if answer:
            self.store.event(self.run_id, "assistant_visible_output", answer)
        self._log("Prompt/visible answer captured")

    def scan_files(self) -> None:
        if not self._require_run():
            return
        if not self.work_folder:
            messagebox.showwarning("Recorder", "Select a work folder first.")
            return
        snapper = FolderSnapshot(self.work_folder)
        after = snapper.capture()
        changes = snapper.diff(self.folder_snapshot_before, after)
        run_artifacts = ARTIFACT_ROOT / self.run_id
        run_artifacts.mkdir(parents=True, exist_ok=True)
        copied: list[str] = []
        for rel in changes["created"] + changes["modified"]:
            source = self.work_folder / rel
            if not source.exists() or not source.is_file():
                continue
            target = run_artifacts / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            try:
                shutil.copy2(source, target)
                copied.append(str(target))
            except (OSError, PermissionError):
                pass
        self.store.event(self.run_id, "file_changes", json.dumps(changes, ensure_ascii=False), {"snapshots": copied})
        self.folder_snapshot_before = after
        self._log(f"Files scanned: +{len(changes['created'])}, ~{len(changes['modified'])}, -{len(changes['deleted'])}")

    def record_correction(self) -> None:
        if not self._require_run():
            return
        correction = simpledialog.askstring("Correction", "What correction did you give ChatGPT?")
        if correction:
            self.store.event(self.run_id, "human_correction", correction)
            self._log("Human correction recorded")

    def finish(self, approved: bool) -> None:
        if not self._require_run():
            return
        final_result = simpledialog.askstring("Final Result", "What was the final result/status?") or ""
        validation = self.validation_var.get().strip()
        self.store.finish(self.run_id, validation, final_result, approved)
        self.store.event(self.run_id, "approval" if approved else "finish", final_result, {"validation": validation})
        self._log("Run approved" if approved else "Run finished")

    def freeze_skill(self) -> None:
        if not self._require_run():
            return
        data = self.store.export_run(self.run_id)
        if not data.get("run", {}).get("approved"):
            if not messagebox.askyesno("Freeze Skill", "This run is not approved. Freeze anyway?"):
                return
        suggested = (data.get("run", {}).get("goal") or "desktop_skill").lower().replace(" ", "_")[:50]
        name = simpledialog.askstring("Skill Name", "Skill folder name:", initialvalue=suggested)
        if not name:
            return
        safe = "".join(ch for ch in name if ch.isalnum() or ch in "_- ").strip().replace(" ", "_") or "desktop_skill"
        target = SKILL_ROOT / safe
        target.mkdir(parents=True, exist_ok=True)
        (target / "reference_run.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        workflow = {
            "name": safe,
            "source": "chatgpt_desktop_companion",
            "goal": data.get("run", {}).get("goal"),
            "validation": data.get("run", {}).get("validation"),
            "requires_human_approval": True,
            "note": "Generated from observable desktop work. Review before production use.",
        }
        (target / "workflow.json").write_text(json.dumps(workflow, ensure_ascii=False, indent=2), encoding="utf-8")
        self.store.event(self.run_id, "skill_frozen", str(target))
        self._log(f"Skill frozen: {target}")
        messagebox.showinfo("Skill Created", f"Created: {target}")


def main() -> None:
    app = ChatGPTDesktopCompanion()
    app.mainloop()


if __name__ == "__main__":
    main()
