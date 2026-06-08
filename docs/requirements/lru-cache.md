# lru-cache — Requirements Ticket

> Locked on 2026-06-08 by requirements-intake. Reopening requires a new autopilot run.

## 1. One-line summary

Add a bounded in-memory LRU cache class (`LruCache`) to `tokenlab` that evicts the least-recently-used entry on capacity overflow and exposes hit/miss/eviction/size statistics.

## 2. Context

`tokenlab` currently has no caching primitive. A general-purpose LRU cache is needed to support callers that want to memoize expensive computations (e.g. token measurements) without pulling in external dependencies. The implementation must stay within the Python 3.12 standard library in keeping with the project's zero-runtime-dependency policy (CONSTITUTION §1).

## 3. In scope

- `LruCache` class at `src/tokenlab/cache.py`.
- `get(key, default=None)` — returns the cached value for `key`, promoting it to MRU; returns `default` (None by default) on a miss. A miss increments the miss counter.
- `put(key, value)` — inserts or updates a key/value pair, promoting the key to MRU. On insert that would exceed capacity, evict the LRU entry first (increments eviction counter). Updating an existing key does NOT increment evictions.
- `stats` read-only property returning a `CacheStats` dataclass with fields: `hits` (int), `misses` (int), `evictions` (int), `size` (int).
- `CacheStats` dataclass defined in the same module.
- `capacity` constructor parameter (required, positional or keyword); must be a positive integer — any value ≤ 0 raises `ValueError`.
- Unit tests at `tests/unit/test_cache.py`.

## 4. Out of scope (explicit non-goals)

- Thread-safety / locking — `LruCache` is explicitly single-threaded.
- `reset_stats()` or any method to clear statistics counters.
- TTL / time-based expiry.
- Async interface.
- Persistent or distributed caching.
- Maximum memory / byte-size limiting (capacity is in number of entries only).
- Typed generics (no `LruCache[K, V]` parameterisation required; plain `Any` key/value is acceptable).
- Any public API beyond `get`, `put`, and `stats`.

## 5. Actors and triggers

- **Caller code** (any module within `tokenlab` or an importing project) constructs an `LruCache(capacity=N)` instance and calls `get`/`put` directly. No event-driven trigger — purely synchronous, on-demand.

## 6. Inputs

| Parameter | Type | Validation |
|---|---|---|
| `capacity` (constructor) | `int` | Must be > 0; raise `ValueError("capacity must be a positive integer")` otherwise. |
| `key` (`get`, `put`) | Any hashable Python object | No additional validation; unhashable keys raise `TypeError` naturally from the underlying dict. |
| `value` (`put`) | Any Python object | No restriction. |
| `default` (`get`) | Any Python object | Optional; defaults to `None`. |

## 7. Outputs

| Method / Property | Return type | Description |
|---|---|---|
| `get(key, default=None)` | `Any` | Cached value, or `default` on miss. |
| `put(key, value)` | `None` | Mutates cache state; returns nothing. |
| `stats` | `CacheStats` | Snapshot of counters and current size. `size` reflects the number of entries currently in the cache (0 ≤ size ≤ capacity). |

`CacheStats` fields: `hits: int`, `misses: int`, `evictions: int`, `size: int`. All counters start at 0 and are non-negative; they never decrement.

## 8. Persistence

None. All state is in-memory and lives for the lifetime of the `LruCache` instance.

## 9. External dependencies

None. Standard library only (CONSTITUTION §1).

## 10. Failure behavior

| Condition | Behavior |
|---|---|
| `capacity <= 0` | Raise `ValueError` in `__init__`. Fatal; instance is not created. |
| `get` on an empty cache or absent key | Return `default`; increment miss counter. Recoverable / expected. |
| `put` when cache is full | Evict the LRU entry, increment eviction counter, then insert the new entry. Recoverable / expected. |
| `get`/`put` called with an unhashable key | Python raises `TypeError` naturally. Caller's responsibility; no special handling. |

No external services means no network/IO failure modes.

## 11. Non-functional constraints

- **Standard library only** (CONSTITUTION §1) — no third-party packages.
- **Single-threaded use only** — no locking is required or provided (agreed A3).
- **Performance (structural):** `get` and `put` must both be O(1) amortized. (CONSTITUTION §6 budgets are TBD for this project, but O(1) is the definitional requirement for an LRU cache and is non-negotiable.)
- **No silent data loss** (CONSTITUTION §2.3) — an eviction is a deliberate, counted operation, not a silent drop.
- **No TODOs left in `main`** (CONSTITUTION §2.5).
- **Observability:** §8a is `always-on`; however, `LruCache` is a pure in-memory utility with no business-meaningful state changes (no actor_id, no resource_id, no external boundary). No structured log events are required for normal cache operations. `spec-architect` should confirm this in the spec §10 observability plan.

## 12. Success criteria

1. `LruCache(capacity=0)` (and any negative capacity) raises `ValueError`.
2. `LruCache(capacity=N)` for N ≥ 1 constructs without error.
3. `get` on a missing key returns the supplied `default` (or `None` when not supplied); `stats.misses` increments by 1.
4. `put` followed by `get` on the same key returns the stored value; `stats.hits` increments by 1 on the `get`.
5. After `put`-ing `N+1` distinct keys into a cache of capacity `N`, the cache contains exactly `N` entries; `stats.size == N`; `stats.evictions == 1`.
6. The evicted entry is the least-recently-used one — verified by confirming that a key accessed (via `get`) before a subsequent set of `put`s is NOT the one evicted when capacity is exceeded.
7. `put` on an existing key updates the value and promotes the key to MRU; `stats.evictions` does NOT increment.
8. `stats` is a `CacheStats` dataclass instance; its fields are integers; `stats.size` equals the current number of stored entries.
9. All counter fields (`hits`, `misses`, `evictions`) start at 0 on a fresh instance.
10. `get` and `put` have O(1) amortized complexity (structural: implementation uses `dict` + `collections.OrderedDict` or equivalent doubly-linked-list approach).

## 13. Answered questions (intake transcript)

| # | Question | Answer |
|---|----------|--------|
| Q1 | Behaviour of `get` on a miss? | Option (b): `get(key, default=None)`; returns `default`; access counts as a miss. |
| Q2 | Stats accessor shape? | Option (c): `CacheStats` dataclass (`hits`, `misses`, `evictions`, `size`) via a read-only `stats` property. |
| Q3 | Thread-safety? | Option (a): No — single-threaded use only; no locking. |

## 14. Inferred assumptions (NOT confirmed by user)

- `capacity` ≤ 0 raises `ValueError` — the rule "capacity required and positive" was stated in the request; the exact exception type is inferred. `(inferred — flag if wrong)`
- Any hashable Python object is a valid key; any Python object is a valid value. No type constraints beyond hashability. `(inferred — flag if wrong)`
- No `reset_stats()` method — stats are monotonically increasing for the lifetime of the instance. `(inferred — flag if wrong)`
- `put` on an existing key updates the value and promotes the key to MRU without incrementing evictions. `(inferred — flag if wrong)`
- `stats.size` reflects the live entry count, not a historical maximum. `(inferred — flag if wrong)`

## 15. Implementer decisions (pin in spec)

These decisions are taken by intake based on the answers above. `spec-architect` MUST record them in the SDD (§5 or §6) and MUST NOT reopen them without a CLARIFY citing a conflict with the constitution or a functional gap.

- **Data structure:** `collections.OrderedDict` (stdlib, O(1) move-to-end on CPython 3.7+). `LruCache.__init__` creates one `OrderedDict` as the internal store.
- **LRU tracking mechanics:** `get` calls `_store.move_to_end(key)` to mark as most-recently-used. `put` on an existing key calls `move_to_end(key)` after updating. `put` on a new key inserts at the end; if `len(_store) > capacity` after insert, pops the first item (`last=False`) as the LRU eviction.
- **Thread-safety:** none — no `threading.Lock` or `contextlib` guards.
- **Stats counters:** plain `int` fields on the instance; `stats` property constructs and returns a fresh `CacheStats` snapshot on each call (not a live view).
- **`CacheStats` definition:** a `@dataclass(frozen=True)` in the same module as `LruCache` so it is importable directly from `src/tokenlab/cache.py`.
