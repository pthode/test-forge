# lru-cache — Requirements Ticket

> Locked on 2026-06-08 by requirements-intake. Reopening requires a new autopilot run.

## 1. One-line summary

Add a bounded in-memory LRU cache class to tokenlab that evicts the least-recently-used entry when capacity is exceeded and exposes cumulative hit/miss/eviction/size statistics.

## 2. Context

tokenlab is a stdlib-only Python 3.12 library. The LRU cache is a general-purpose primitive to be used internally and by library consumers for bounding memory use in key→value lookup scenarios. There is no existing caching primitive in the codebase. It replaces ad-hoc dict usage in contexts where eviction under memory pressure is required.

## 3. In scope

- `LruCache` class at `src/tokenlab/cache.py`, importable as `from tokenlab.cache import LruCache`.
- Constructor: `LruCache(capacity: int)` — sets a fixed maximum number of entries.
- `get(key, default=None)` — returns the value if the key exists (promoting it to MRU), otherwise returns `default`.
- `put(key, value)` — inserts or updates the entry and promotes it to MRU. If the cache is at capacity and the key is new, evicts the LRU entry first.
- `stats()` — returns a dataclass or namedtuple with fields `hits`, `misses`, `evictions`, `size` (current entry count).
- Cumulative stats tracked from construction; no reset mechanism.
- Raising `ValueError` on construction when `capacity` is 0 or negative.
- Unit tests at `tests/unit/test_cache.py`.

## 4. Out of scope (explicit non-goals)

- Thread safety — no internal locking; callers are responsible for external synchronization.
- TTL/expiry — entries do not expire by time.
- Runtime type-checking of keys or values.
- A stats-reset method.
- Any persistence (in-memory only; nothing survives process restart).
- Monitoring instrumentation or structured log events (this is a pure in-memory utility with no I/O boundary; §8a operational observability does not apply here).
- Any public API beyond `__init__`, `get`, `put`, and `stats`.

## 5. Actors and triggers

- **Library consumer (developer)** — instantiates `LruCache`, calls `get`/`put`/`stats` in application code.
- **test-engineer** — drives the class via pytest unit tests.
- No end-users, no HTTP surface, no external actors.

## 6. Inputs

| Method | Parameter | Type | Validation |
|--------|-----------|------|------------|
| `__init__` | `capacity` | `int` | Must be ≥ 1; raises `ValueError` if 0 or negative. Immutable after construction. |
| `get` | `key` | `Hashable` | No runtime type-check; any hashable value is accepted. |
| `get` | `default` | `Any` | Optional; defaults to `None`. |
| `put` | `key` | `Hashable` | No runtime type-check. |
| `put` | `value` | `Any` | Unrestricted. |

## 7. Outputs

| Method | Return type | Description |
|--------|-------------|-------------|
| `get` | `Any` | The stored value if key present (key promoted to MRU); otherwise `default`. |
| `put` | `None` | No return value. Side effects: insert/update entry, evict LRU if necessary. |
| `stats()` | dataclass or namedtuple | Fields: `hits: int`, `misses: int`, `evictions: int`, `size: int`. |

`size` reports the current number of entries (not bytes). Stats are cumulative from construction.

## 8. Persistence

None. The cache is purely in-memory. All state is lost when the instance is garbage-collected or the process exits.

## 9. External dependencies

None. Standard library only (`collections.OrderedDict` or equivalent stdlib primitives). No third-party packages.

## 10. Failure behavior

| Condition | Behavior |
|-----------|----------|
| `LruCache(0)` or `LruCache(-n)` | Raises `ValueError` at construction time. |
| `get` on missing key | Returns `default` (no exception); increments `misses`. |
| `put` on existing key | Updates value in place, promotes key to MRU, does NOT increment `evictions`. |
| `put` on new key when at capacity | Evicts LRU entry first (increments `evictions`), then inserts new entry. |

No recoverable/fatal distinction beyond the above; there are no I/O boundaries or external services that can fail.

## 11. Non-functional constraints

- **Standard library only** (CONSTITUTION §1) — no third-party runtime or test dependencies.
- **Python 3.12** (CONSTITUTION §1) — no syntax or APIs beyond 3.12 stdlib.
- **No `# TODO` in `main`** (CONSTITUTION §2.5).
- **Naming style** (CONSTITUTION §3): full words, one purpose per function.
- **Comments explain why, not what** (CONSTITUTION §3).
- **Coverage:** tracked but not gated (CONSTITUTION §4 — floor is 0%; aim for high unit coverage given the small, pure surface).
- **Performance budgets** (CONSTITUTION §6): TBD for this library; `O(1)` amortized for `get` and `put` is the standard LRU contract and is expected by downstream consumers. `performance-analyst` will flag non-O(1) implementations as a structural issue.
- **Accessibility:** N/A — no UI surface (CONSTITUTION §7.2).
- **Observability:** §8a operational observability does not apply to a pure in-memory utility with no I/O boundary. No structured log events are required for this feature.

## 12. Success criteria

1. `from tokenlab.cache import LruCache` succeeds with no import errors on Python 3.12.
2. `LruCache(0)` raises `ValueError`; `LruCache(-1)` raises `ValueError`; `LruCache(1)` constructs without error.
3. `get` on a missing key returns `None` when no default is supplied and increments `stats().misses`.
4. `get` on a missing key returns the supplied default value and increments `stats().misses`.
5. `get` on a present key returns the correct value, promotes the key to MRU, and increments `stats().hits`.
6. `put` on a new key inserts the entry; subsequent `get` returns the value.
7. `put` on an existing key updates the value and promotes to MRU without incrementing `stats().evictions`.
8. When the cache is at capacity, `put` of a new key evicts the least-recently-used entry (not most-recently-used) and increments `stats().evictions` by 1.
9. `stats().size` equals the current number of entries (not capacity).
10. Stats are cumulative: multiple hits, misses, and evictions across calls are summed correctly in `stats()`.
11. A cache with `capacity=1`: `put(A)`, `put(B)` results in `A` being evicted and only `B` being retrievable.
12. Access ordering: after `put(A)`, `put(B)`, `get(A)` (making A MRU), `put(C)` should evict B (LRU), not A.
13. All unit tests pass under `pytest` with no external dependencies.
14. The implementation uses only the Python 3.12 standard library.

## 13. Answered questions (intake transcript)

| # | Question | Answer |
|---|----------|--------|
| Q1 | How should stats be exposed? | `stats()` method returning a dataclass or namedtuple with fields `hits`, `misses`, `evictions`, `size`. |
| Q2 | Should the cache make a documented thread-safety guarantee? | No thread-safety guarantee — callers are responsible for external locking. |
| Q3 | What types are valid for keys and values? | Keys must be hashable (`Hashable`); values unrestricted (`Any`); no runtime type-checking. |
| Q4 | What should happen when `get(key)` is called for a missing key? | Accept an optional `default` parameter (like `dict.get`), returning `None` if not supplied. |
| Q5 | Is a capacity of 0 a valid construction argument? | No — `LruCache(0)` raises `ValueError` at construction time; negative capacity likewise. |

## 14. Inferred assumptions (NOT confirmed by user)

- `from tokenlab.cache import LruCache` is the canonical import path. (inferred — flag if wrong)
- `capacity` is immutable after construction; no resize method is provided. (inferred — flag if wrong)
- `put` on an existing key updates the value and promotes to MRU but does NOT increment `evictions`. (inferred — flag if wrong)
- Stats are cumulative from construction; there is no reset method. (inferred — flag if wrong)
- No TTL or time-based expiry is supported. (inferred — flag if wrong)
- `stats().size` reports entry count, not bytes consumed. (inferred — flag if wrong)
- Negative capacity raises the same `ValueError` as zero capacity. (inferred — flag if wrong)
