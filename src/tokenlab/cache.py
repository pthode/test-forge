"""Bounded in-memory LRU cache for tokenlab (stdlib-only, single-threaded)."""

from collections import OrderedDict
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class CacheStats:
    hits: int
    misses: int
    evictions: int
    size: int


class LruCache:
    def __init__(self, capacity: int) -> None:
        if capacity <= 0:
            raise ValueError("capacity must be a positive integer")
        self.capacity = capacity
        self._store: OrderedDict[Any, Any] = OrderedDict()
        self._hits = 0
        self._misses = 0
        self._evictions = 0

    def get(self, key: Any, default: Any = None) -> Any:
        if key in self._store:
            self._store.move_to_end(key)
            self._hits += 1
            return self._store[key]
        self._misses += 1
        return default

    def put(self, key: Any, value: Any) -> None:
        if key in self._store:
            self._store[key] = value
            self._store.move_to_end(key)
            return
        self._store[key] = value
        if len(self._store) > self.capacity:
            self._store.popitem(last=False)
            self._evictions += 1

    @property
    def stats(self) -> CacheStats:
        return CacheStats(
            hits=self._hits,
            misses=self._misses,
            evictions=self._evictions,
            size=len(self._store),
        )
