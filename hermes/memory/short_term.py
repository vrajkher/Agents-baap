from __future__ import annotations

from collections import deque
from typing import Any, Iterable


class ShortTermMemory:
    """Bounded in-memory event log for active task context."""

    def __init__(self, capacity: int = 256) -> None:
        self._buffer: deque[dict[str, Any]] = deque(maxlen=capacity)

    def push(self, event: dict[str, Any]) -> None:
        self._buffer.append(event)

    def recent(self, n: int = 10) -> list[dict[str, Any]]:
        n = max(0, n)
        return list(self._buffer)[-n:]

    def clear(self) -> None:
        self._buffer.clear()

    def __iter__(self) -> Iterable[dict[str, Any]]:
        return iter(self._buffer)

    def __len__(self) -> int:
        return len(self._buffer)
