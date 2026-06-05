"""A bounded, in-memory least-recently-used cache primitive (not thread-safe)."""

from collections import OrderedDict
from typing import Any

__all__ = ["LruCache"]


class LruCache:
    """A fixed-capacity cache that evicts the least-recently-used entry on overflow.

    Stores hashable ``key`` to arbitrary ``value`` mappings up to a fixed positive
    ``capacity``. Recency is true-LRU: a ``get`` hit and any ``put`` mark the touched
    entry most-recently-used, and inserting a new key while full evicts the entry left
    untouched the longest. ``None`` is a storable value distinct from an absent key.

    Lifetime statistics are exposed as read-only properties: ``hits``, ``misses``,
    ``evictions``, ``size`` (current entry count, also ``len(cache)``), and ``capacity``.
    ``reset_stats`` zeroes the three counters without dropping entries; ``clear`` drops
    entries without touching the counters.

    Constructing with a ``capacity`` below ``1`` raises ``ValueError``. Passing an
    unhashable key to any key-accepting method surfaces the underlying mapping's natural
    ``TypeError``, unwrapped.

    This class is NOT thread-safe; it acquires no internal lock. A caller sharing one
    instance across threads must serialize access itself.
    """

    def __init__(self, capacity: int) -> None:
        """Create an empty cache bounded to ``capacity`` entries.

        ``capacity`` must be an integer of at least ``1``; a value below ``1`` raises
        ``ValueError``. The cache starts empty with all counters at zero.
        """
        if capacity < 1:
            raise ValueError(f"capacity must be >= 1, got {capacity!r}")
        self._store: OrderedDict[Any, Any] = OrderedDict()
        self._capacity = capacity
        self._hits = 0
        self._misses = 0
        self._evictions = 0

    def get(self, key: Any, default: Any = None) -> Any:
        """Return the value for ``key`` on a hit, refreshing its recency, else ``default``.

        On a hit the entry becomes most-recently-used and ``hits`` increments by one; the
        stored value is returned (which may itself be ``None``). On a miss ``misses``
        increments by one, the key is not inserted, no exception is raised, and ``default``
        (``None`` when omitted) is returned.
        """
        if key in self._store:
            self._store.move_to_end(key)
            self._hits += 1
            return self._store[key]
        self._misses += 1
        return default

    def put(self, key: Any, value: Any) -> None:
        """Insert or overwrite ``key`` with ``value``, marking the entry most-recently-used.

        Overwriting an existing key updates its value and refreshes recency without growing
        ``size``. Inserting a new key while ``size == capacity`` first evicts the
        least-recently-used entry and increments ``evictions`` by one, then inserts the new
        entry, leaving ``size == capacity``.
        """
        if key in self._store:
            self._store[key] = value
            self._store.move_to_end(key)
            return
        if len(self._store) >= self._capacity:
            self._store.popitem(last=False)
            self._evictions += 1
        self._store[key] = value

    def peek(self, key: Any, default: Any = None) -> Any:
        """Return the value for ``key`` without affecting recency or the hit/miss counters.

        Returns the stored value if present (possibly ``None``), otherwise ``default``. Does
        not move the entry in recency order and does not change ``hits`` or ``misses``.
        """
        if key in self._store:
            return self._store[key]
        return default

    def remove(self, key: Any) -> bool:
        """Remove ``key`` if present, returning whether it was there.

        Removing a present entry reduces ``size`` by one and returns ``True``. On an absent
        key this is a no-op returning ``False``; it never raises.
        """
        if key in self._store:
            del self._store[key]
            return True
        return False

    def clear(self) -> None:
        """Drop all cached entries (``size`` becomes ``0``) without touching counters.

        ``capacity`` is unchanged and ``hits``/``misses``/``evictions`` are NOT reset; call
        ``reset_stats`` separately to zero the counters.
        """
        self._store.clear()

    def reset_stats(self) -> None:
        """Zero the ``hits``, ``misses``, and ``evictions`` counters without dropping entries.

        Cached entries, ``size``, and ``capacity`` are unaffected; subsequent operations
        resume counting from zero.
        """
        self._hits = 0
        self._misses = 0
        self._evictions = 0

    def __contains__(self, key: Any) -> bool:
        """Report whether ``key`` is cached without affecting recency or counters."""
        return key in self._store

    def __len__(self) -> int:
        """Return the current entry count (equivalent to ``size``)."""
        return len(self._store)

    @property
    def hits(self) -> int:
        """Cumulative count of ``get`` hits since construction or the last ``reset_stats``."""
        return self._hits

    @property
    def misses(self) -> int:
        """Cumulative count of ``get`` misses since construction or the last ``reset_stats``."""
        return self._misses

    @property
    def evictions(self) -> int:
        """Cumulative count of evictions since construction or the last ``reset_stats``."""
        return self._evictions

    @property
    def size(self) -> int:
        """Current number of cached entries."""
        return len(self._store)

    @property
    def capacity(self) -> int:
        """Maximum number of entries the cache holds before evicting on a new insert."""
        return self._capacity
