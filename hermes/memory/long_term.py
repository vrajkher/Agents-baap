from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Any


class LongTermMemory:
    """Structured JSON long-term store.

    The framework treats vector databases as a pluggable optional backend.
    For the default local-first deployment we persist a single JSON document
    keyed by agent/task so that memory is inspectable without extra tooling.
    """

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self._lock = threading.Lock()
        self._data: dict[str, Any] = {}
        if self.path.exists():
            self._data = json.loads(self.path.read_text(encoding="utf-8") or "{}")

    def store(self, key: str, value: Any) -> None:
        with self._lock:
            self._data[key] = value
            self._flush()

    def retrieve(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)

    def update(self, key: str, **fields: Any) -> None:
        with self._lock:
            current = self._data.get(key)
            if not isinstance(current, dict):
                current = {}
            current.update(fields)
            self._data[key] = current
            self._flush()

    def summarize(self, prefix: str = "") -> dict[str, Any]:
        matches = {k: v for k, v in self._data.items() if k.startswith(prefix)}
        return {
            "count": len(matches),
            "keys": sorted(matches),
            "prefix": prefix,
        }

    def _flush(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self._data, indent=2, default=str), encoding="utf-8")
