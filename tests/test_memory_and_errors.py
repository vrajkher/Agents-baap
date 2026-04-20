from pathlib import Path

import pytest

from hermes.errors.handler import ErrorHandler
from hermes.memory.long_term import LongTermMemory
from hermes.memory.short_term import ShortTermMemory


def test_short_term_memory_is_bounded() -> None:
    mem = ShortTermMemory(capacity=3)
    for i in range(5):
        mem.push({"i": i})
    assert len(mem) == 3
    assert mem.recent(2) == [{"i": 3}, {"i": 4}]


def test_long_term_memory_persists(tmp_path: Path) -> None:
    path = tmp_path / "mem.json"
    mem = LongTermMemory(path)
    mem.store("agent:1", {"result": "ok"})
    mem.update("agent:1", score=0.9)

    reloaded = LongTermMemory(path)
    assert reloaded.retrieve("agent:1") == {"result": "ok", "score": 0.9}
    assert reloaded.summarize("agent:")["count"] == 1


def test_error_handler_retries_and_falls_back() -> None:
    handler = ErrorHandler(max_retries=2, backoff=0)
    calls = {"n": 0}

    def flaky() -> int:
        calls["n"] += 1
        raise RuntimeError("nope")

    result = handler.run_with_retry(flaky, agent_name="a", fallback=lambda: 99)
    assert result == 99
    assert calls["n"] == 2
    assert len(handler.log) == 2


def test_error_handler_raises_when_no_fallback() -> None:
    handler = ErrorHandler(max_retries=1, backoff=0)

    def boom() -> None:
        raise ValueError("x")

    with pytest.raises(ValueError):
        handler.run_with_retry(boom, agent_name="b")
