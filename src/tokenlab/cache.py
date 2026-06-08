"""Bounded in-memory least-recently-used cache primitive.

Provides :class:`LruCache`, a fixed-capacity key->value store that evicts the
least-recently-used entry when a new key is inserted at capacity, and exposes
cumulative hit/miss/eviction/size statistics via :class:`CacheStats`.
"""

from collections import OrderedDict
from dataclasses import dataclass
from typing import Any, Hashable


@dataclass(frozen=True)
class CacheStats:
    """Immutable point-in-time snapshot of a cache's cumulative counters.

    Fields:
        hits: Cumulative count of ``get`` calls that found a present key.
        misses: Cumulative count of ``get`` calls on an absent key.
        evictions: Cumulative count of least-recently-used entries dropped.
        size: Current number of stored entries (entry count, never capacity
            or bytes).

    ``hits``, ``misses``, and ``evictions`` accumulate from construction with
    no reset mechanism; ``size`` reflects the cache state at the moment
    ``stats`` was called.
    """

    hits: int
    misses: int
    evictions: int
    size: int


class LruCache:
    """Fixed-capacity in-memory cache with least-recently-used eviction.

    An ``LruCache`` maps hashable keys to arbitrary values, holding at most
    ``capacity`` entries. When a new key is inserted while the cache is full,
    the least-recently-used (LRU) entry is evicted first. Recency is updated by
    both ``get`` (on a present key) and ``put`` (on any key), so the entry
    evicted is always the one least recently touched by either method.

    The cache is purely in-memory: it performs no I/O and persists nothing.
    It makes no thread-safety guarantee; callers needing concurrent access
    must synchronize externally. Keys must be hashable; values are
    unrestricted. No runtime type-checking of keys, values, or defaults is
    performed -- a non-hashable key surfaces the standard ``TypeError`` from
    the underlying mapping.
    """

    def __init__(self, capacity: int) -> None:
        """Construct an empty cache holding at most ``capacity`` entries.

        Args:
            capacity: The fixed maximum number of entries. Must be >= 1.
                It is immutable after construction; no resize method exists.

        Raises:
            ValueError: If ``capacity`` is zero or negative.
        """
        if capacity <= 0:
            raise ValueError(f"capacity must be >= 1, got {capacity}")
        self._capacity = capacity
        self._entries: OrderedDict[Hashable, Any] = OrderedDict()
        self._hits = 0
        self._misses = 0
        self._evictions = 0

    def get(self, key: Hashable, default: Any = None) -> Any:
        """Return the value stored for ``key``, promoting it to most-recently-used.

        Args:
            key: The key to look up. Must be hashable.
            default: The value returned when ``key`` is absent. Defaults to
                ``None``.

        Returns:
            The stored value if ``key`` is present, otherwise ``default``.

        On a hit, ``key`` becomes most-recently-used and ``stats().hits`` is
        incremented. On a miss, ``default`` is returned, ``stats().misses`` is
        incremented, and ordering, size, and evictions are left unchanged. No
        exception is raised for an absent key.
        """
        if key in self._entries:
            self._entries.move_to_end(key)
            self._hits += 1
            return self._entries[key]
        self._misses += 1
        return default

    def put(self, key: Hashable, value: Any) -> None:
        """Insert or update ``key`` and promote it to most-recently-used.

        Args:
            key: The key to store. Must be hashable.
            value: The value to associate with ``key``. Unrestricted.

        Returns:
            ``None``.

        If ``key`` already exists, its value is updated in place, it is
        promoted to most-recently-used, and ``stats().evictions`` is left
        unchanged. If ``key`` is new and the cache is at capacity, the
        least-recently-used entry is evicted first (``stats().evictions``
        incremented by one) before the new entry is inserted as
        most-recently-used.
        """
        if key in self._entries:
            self._entries[key] = value
            self._entries.move_to_end(key)
            return
        if len(self._entries) == self._capacity:
            self._entries.popitem(last=False)
            self._evictions += 1
        self._entries[key] = value

    def stats(self) -> CacheStats:
        """Return an immutable snapshot of the cache's cumulative counters.

        Returns:
            A :class:`CacheStats` carrying cumulative ``hits``, ``misses``, and
            ``evictions`` (counted from construction) and the current ``size``
            (the entry count at call time).
        """
        return CacheStats(
            hits=self._hits,
            misses=self._misses,
            evictions=self._evictions,
            size=len(self._entries),
        )
