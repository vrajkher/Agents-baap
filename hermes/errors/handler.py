from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Callable

log = logging.getLogger("hermes.errors")


@dataclass
class FailureRecord:
    agent: str
    attempt: int
    error: str
    timestamp: float = field(default_factory=time.time)


class ErrorHandler:
    """Retry-with-fallback wrapper. Records each failure for later analysis."""

    def __init__(self, max_retries: int = 3, backoff: float = 0.1) -> None:
        self.max_retries = max_retries
        self.backoff = backoff
        self.log: list[FailureRecord] = []

    def run_with_retry(
        self,
        fn: Callable[[], Any],
        *,
        agent_name: str,
        fallback: Callable[[], Any] | None = None,
    ) -> Any:
        last_error: Exception | None = None
        for attempt in range(1, self.max_retries + 1):
            try:
                return fn()
            except Exception as exc:
                last_error = exc
                self.log.append(FailureRecord(agent=agent_name, attempt=attempt, error=str(exc)))
                log.warning("agent=%s attempt=%s failed: %s", agent_name, attempt, exc)
                time.sleep(self.backoff * attempt)
        if fallback is not None:
            log.warning("agent=%s exhausted retries; invoking fallback", agent_name)
            return fallback()
        assert last_error is not None
        raise last_error
