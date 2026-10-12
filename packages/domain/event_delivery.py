"""At-least-once consumer inbox contract and deterministic memory adapter."""

from __future__ import annotations

import threading
from typing import Protocol

from packages.runtime.src.lengeas_runtime.events import InboxKey


class ConsumerInbox(Protocol):
    def record_once(self, key: InboxKey) -> bool: ...


class InMemoryConsumerInbox:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._records: set[InboxKey] = set()

    def record_once(self, key: InboxKey) -> bool:
        with self._lock:
            if key in self._records:
                return False
            self._records.add(key)
            return True
