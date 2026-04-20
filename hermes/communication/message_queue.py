from __future__ import annotations

import json
import queue
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class Message:
    sender: str
    recipient: str
    event: str
    payload: dict[str, Any] = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = field(default_factory=time.time)

    def to_json(self) -> str:
        return json.dumps(
            {
                "id": self.id,
                "sender": self.sender,
                "recipient": self.recipient,
                "event": self.event,
                "payload": self.payload,
                "timestamp": self.timestamp,
            }
        )


class MessageQueue:
    """In-process queue for agent-to-agent communication with event subscribers."""

    def __init__(self) -> None:
        self._queue: queue.Queue[Message] = queue.Queue()
        self._subscribers: dict[str, list[Callable[[Message], None]]] = {}

    def publish(self, message: Message) -> None:
        self._queue.put(message)
        for callback in self._subscribers.get(message.event, []):
            callback(message)
        for callback in self._subscribers.get("*", []):
            callback(message)

    def subscribe(self, event: str, callback: Callable[[Message], None]) -> None:
        self._subscribers.setdefault(event, []).append(callback)

    def pop(self, timeout: float | None = None) -> Message | None:
        try:
            return self._queue.get(timeout=timeout)
        except queue.Empty:
            return None

    def __len__(self) -> int:
        return self._queue.qsize()
