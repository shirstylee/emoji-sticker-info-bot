from __future__ import annotations

import time
from collections import OrderedDict
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from typing import Any

from aiogram.fsm.state import State
from aiogram.fsm.storage.base import BaseStorage, StateType, StorageKey


@dataclass(slots=True)
class _Record:
    expires_at: float
    state: str | None = None
    data: dict[str, Any] = field(default_factory=dict)


class AdminStateStorage(BaseStorage):
    """Bounded, expiring input sessions; idle reads never allocate a record."""

    def __init__(self, *, ttl_seconds: float = 600, max_items: int = 100,
                 clock: Callable[[], float] = time.monotonic) -> None:
        if ttl_seconds <= 0 or max_items < 1:
            raise ValueError("Session limits must be positive")
        self._ttl = ttl_seconds
        self._max_items = max_items
        self._clock = clock
        self._records: OrderedDict[StorageKey, _Record] = OrderedDict()

    def _get(self, key: StorageKey) -> _Record | None:
        now = self._clock()
        for expired in [key for key, record in self._records.items() if record.expires_at <= now]:
            self._records.pop(expired)
        return self._records.get(key)

    def _save(self, key: StorageKey, record: _Record) -> None:
        if record.state is None and not record.data:
            self._records.pop(key, None)
            return
        record.expires_at = self._clock() + self._ttl
        self._records[key] = record
        self._records.move_to_end(key)
        while len(self._records) > self._max_items:
            self._records.popitem(last=False)

    async def set_state(self, key: StorageKey, state: StateType = None) -> None:
        record = self._get(key) or _Record(0)
        record.state = state.state if isinstance(state, State) else state
        self._save(key, record)

    async def get_state(self, key: StorageKey) -> str | None:
        record = self._get(key)
        return record.state if record else None

    async def set_data(self, key: StorageKey, data: Mapping[str, Any]) -> None:
        record = self._get(key) or _Record(0)
        record.data = dict(data)
        self._save(key, record)

    async def get_data(self, key: StorageKey) -> dict[str, Any]:
        record = self._get(key)
        return record.data.copy() if record else {}

    async def close(self) -> None:
        self._records.clear()
