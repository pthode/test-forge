# lru-cache — Software Design Document

> Source ticket: `/docs/requirements/lru-cache.md` (locked 2026-06-08).
> Constitution refs: §1 stack (Python 3.12, stdlib-only, pytest), §2 non-negotiables, §3 style, §5 security, §6 perf (budgets TBD), §8a observability (always-on). No `§P` project sections defined.

## 1. Context

`tokenlab` has no caching primitive. This feature adds a bounded, in-memory, single-threaded LRU (least-recently-used) cache class, `LruCache`, so callers can memoize expensive computations (e.g. token measurements) without pulling in external dependencies. The implementation stays within the Python 3.12 standard library per CONSTITUTION §1 (zero runtime dependencies).

The cache has a fixed entry-count capacity set at construction. When inserting a new key would exceed capacity, the least-recently-used entry is evicted (counted, never silently dropped — CONSTITUTION §2.3). The class exposes hit/miss/eviction/size statistics via a read-only `stats` property.

**This feature explicitly does NOT** provide thread-safety, TTL/expiry, async interfaces, byte-size limiting, persistence, typed generics, stats reset, or any public surface beyond `get`, `put`, and `stats`. See §3.

## 2. Requirements

<!-- Sources map each Rn back to the ticket item it derives from. -->

- R1: `LruCache(capacity)` accepts `capacity` as a required positional-or-keyword `int`. Any `capacity <= 0` raises `ValueError("capacity must be a positive integer")` in `__init__`; the instance is not created. _(Sources: ticket §3, §6, §10, §12.1, §14 inferred-1)_
- R2: `LruCache(capacity=N)` for any integer `N >= 1` constructs successfully with an empty cache and all counters at 0. _(Sources: ticket §3, §12.2, §12.9)_
- R3: `get(key, default=None)` returns the stored value for `key` and promotes that key to most-recently-used (MRU); on a hit, `hits` increments by 1. _(Sources: ticket §3, §7, §12.4)_
- R4: `get(key, default=None)` on a missing key returns `default` (which is `None` when the caller omits it) and increments `misses` by 1. A miss does not mutate stored entries or ordering. _(Sources: ticket §3, §6, §10, §12.3, §13 Q1)_
- R5: `put(key, value)` inserts a new key/value pair or updates an existing key, and in both cases promotes the key to MRU. Returns `None`. _(Sources: ticket §3, §7, §12.7)_
- R6: When `put` inserts a NEW key into a cache already at capacity, the LRU entry is evicted before/around the insert, `evictions` increments by 1, and the resulting `size` equals `capacity`. The evicted entry is exactly the least-recently-used one. _(Sources: ticket §3, §10, §11, §12.5, §12.6)_
- R7: `put` on an EXISTING key updates the value and promotes it to MRU without incrementing `evictions` and without changing `size`. _(Sources: ticket §3, §12.7, §14 inferred-4)_
- R8: `stats` is a read-only property that returns a fresh `CacheStats` instance on each access (a snapshot, not a live view), with integer fields `hits`, `misses`, `evictions`, `size`. `size` reflects the current live entry count (`0 <= size <= capacity`). _(Sources: ticket §3, §7, §12.8, §13 Q2, §14 inferred-5)_
- R9: All counters (`hits`, `misses`, `evictions`) start at 0 on a fresh instance, are non-negative, and never decrement over the lifetime of the instance (no reset mechanism exists). _(Sources: ticket §3, §7, §12.9, §14 inferred-3)_
- R10: `get` and `put` are O(1) amortized. Structural requirement, non-negotiable for an LRU cache (CONSTITUTION §6 budgets are TBD but O(1) is definitional). _(Sources: ticket §11, §12.10)_
- R11: Keys may be any hashable Python object and values any Python object; no type validation beyond hashability is performed. An unhashable key raises `TypeError` naturally from the underlying mapping — no special handling. _(Sources: ticket §6, §10, §14 inferred-2)_
- R12: `CacheStats` is a frozen dataclass defined in the same module (`src/tokenlab/cache.py`) and importable directly from it. _(Sources: ticket §3, §15 CacheStats definition)_

## 3. Non-goals

- Thread-safety / locking — `LruCache` is single-threaded only (ticket §4, §13 Q3).
- `reset_stats()` or any counter-clearing method (ticket §4, §14 inferred-3).
- TTL / time-based expiry (ticket §4).
- Async interface (ticket §4).
- Persistence / distributed caching (ticket §4, §8).
- Byte-size / memory-based capacity (capacity is entry-count only) (ticket §4).
- Typed generics (`LruCache[K, V]`) — plain `Any` key/value is acceptable (ticket §4).
- Any public API beyond `get`, `put`, `stats` (ticket §4).

## 4. Architecture

Single module, single product class, single supporting dataclass — no multi-component collaboration, so no sequence diagram is required (fewer than 3 collaborators).

```
src/tokenlab/cache.py
├── CacheStats   (frozen dataclass: hits, misses, evictions, size — all int)
└── LruCache
    ├── __init__(self, capacity: int)
    │     validates capacity > 0; raises ValueError otherwise
    │     creates internal collections.OrderedDict store + int counters
    ├── get(self, key, default=None) -> Any
    ├── put(self, key, value) -> None
    └── stats (property) -> CacheStats   (fresh snapshot per access)
```

Internal collaborators: one `collections.OrderedDict` (the store) and three plain `int` counters (`_hits`, `_misses`, `_evictions`). `size` is derived from `len(store)` at snapshot time — not stored separately — so it can never drift from the actual entry count.

## 5. API contract

No HTTP API — this is an in-process library class. No OpenAPI artifact. Public Python surface:

```python
@dataclass(frozen=True)
class CacheStats:
    hits: int
    misses: int
    evictions: int
    size: int

class LruCache:
    def __init__(self, capacity: int) -> None: ...
    def get(self, key: Any, default: Any = None) -> Any: ...
    def put(self, key: Any, value: Any) -> None: ...
    @property
    def stats(self) -> CacheStats: ...
```

### 5.1 Pinned implementer decisions (from ticket §15 + §14)

These are locked by intake; recorded here for the autopilot final-report disclosure. `developer` MUST follow them; reopening requires a CLARIFY citing a constitution conflict or functional gap.

| # | Decision | Rationale (one line) |
|---|---|---|
| D1 | **Data structure:** internal store is a single `collections.OrderedDict`. | Stdlib, O(1) `move_to_end` and O(1) `popitem` on CPython 3.7+ — satisfies R10 with no third-party dependency (CONSTITUTION §1). |
| D2 | **LRU mechanics:** `get` hit calls `store.move_to_end(key)`; `put` on existing key updates then `move_to_end(key)`; `put` on new key assigns at end, and if `len(store) > capacity` after insert, `store.popitem(last=False)` evicts the LRU entry. | Standard OrderedDict LRU idiom; insert-then-trim keeps the new key from being a candidate for its own eviction, satisfying R6's "evicted entry is exactly the LRU one". |
| D3 | **Thread-safety model:** none — no `threading.Lock`, no `contextlib` guards. | Ticket §4 / §13 Q3 declare single-threaded use out of scope; adding locking would contradict the locked non-goal. |
| D4 | **Eviction mechanics:** eviction is via `popitem(last=False)` and `_evictions += 1`; an update of an existing key never evicts. | Counted, non-silent (CONSTITUTION §2.3); satisfies R6/R7. |
| D5 | **Exception classes:** only `ValueError` is raised explicitly (invalid capacity, R1). `TypeError` for unhashable keys is allowed to propagate naturally from the dict; no custom exception classes are introduced. | Ticket §6/§10/§14 inferred-1; introducing custom exceptions would exceed the locked surface and add no caller value. |
| D6 | **Stats representation:** three private `int` counters on the instance (`_hits`, `_misses`, `_evictions`); `size` derived from `len(store)`; `stats` property constructs a fresh frozen `CacheStats` each call. | Snapshot-not-live (R8) prevents callers mutating internal state; deriving `size` avoids drift; frozen dataclass gives value semantics and immutability. |
| D7 | **Module layout:** both `CacheStats` and `LruCache` live in `src/tokenlab/cache.py`; absolute import path `tokenlab.cache`. | Ticket §15; CONSTITUTION §3 (absolute imports from project root). |
| D8 | **Capacity attribute exposure:** `capacity` stored as a public read-only-by-convention instance attribute `self.capacity`; not part of the mandated surface but harmless and aids debugging/tests. | Technical method, in-stack; no behavior change. If review objects it can be made private without spec change. |
| D9 | **Class name `LruCache` (deliberate §3 deviation):** the class is named `LruCache`, NOT the §3-conformant `LRUCache`. This is intentional and accepted. | `LRU` is a ≤3-letter acronym, so CONSTITUTION §3 ("acronyms ≤3 letters stay uppercase") would prescribe `LRUCache`. However the name `LruCache` is the user's **literal locked requirement** (ticket §1, §3), not a free spec choice, and matches stdlib precedent (`functools.lru_cache`). §3 is a style anchor (guidance), not a §2 non-negotiable; it does not authorize silently overwriting an explicit locked user requirement. The deviation is a tracked **minor** (BACKLOG `B-008`), NOT an unresolved major. A `§P` exception is intentionally NOT used: per §11.2 a project section may not contradict §3, so it cannot grant this carve-out. Resolution path if ever reversed: a §11.1 forge amendment or a new autopilot run re-locking the name. |

## 6. Data model

No persisted state. All state is in-memory for the lifetime of the `LruCache` instance (ticket §8). No data-model artifact required.

## 7. Failure modes

- **Input validation (R1):** `capacity <= 0` (including non-positive ints) → raise `ValueError("capacity must be a positive integer")` in `__init__`; instance not created. Fatal, caller-facing. Non-int `capacity` is out of scope for explicit handling — passing a non-int is a programming error; comparison/usage will raise naturally (`TypeError`). Documented, not specially handled.
- **Miss (R4):** `get` on empty cache or absent key → return `default`, increment `misses`. Expected/recoverable; not an error.
- **Capacity overflow (R6):** `put` of a new key at capacity → evict LRU, increment `evictions`, insert. Expected/recoverable; counted, never silent (CONSTITUTION §2.3).
- **Unhashable key (R11):** `get`/`put` with an unhashable key → `TypeError` propagates from the underlying dict. Caller's responsibility; no catch-and-swallow (CONSTITUTION §3 errors-at-boundary).
- **External-service failure:** N/A — no network, no I/O, no external services.
- **Concurrency:** out of scope — single-threaded contract (D3). Behavior under concurrent access is explicitly undefined and not tested.

## 8. Acceptance criteria

1:1 mapping to requirements (criteria also align to ticket §12):

- R1 → `LruCache(capacity=0)` and `LruCache(capacity=-1)` each raise `ValueError`; no instance is bound.
- R2 → `LruCache(capacity=N)` for `N in {1, 2, 100}` constructs; immediately `stats == CacheStats(0, 0, 0, 0)`.
- R3 → after `put("a", 1)`, `get("a")` returns `1` and `stats.hits == 1`; the accessed key is now MRU.
- R4 → `get("absent")` returns `None`; `get("absent", "x")` returns `"x"`; each call increments `stats.misses` by 1; stored entries unchanged.
- R5 → `put` then `get` round-trips the value; a second `put` on the same key with a new value, then `get`, returns the new value.
- R6 → into capacity `N=2`: `put("a",1); put("b",2); put("c",3)` leaves `size == 2`, `evictions == 1`, and `"a"` (the LRU) absent while `"b"`,`"c"` present.
- R6 (LRU correctness) → `put("a",1); put("b",2); get("a"); put("c",3)` evicts `"b"` (now LRU), not `"a"` (recently accessed). `get("a")` still hits.
- R7 → into capacity `N=2`: `put("a",1); put("b",2); put("a",9)` leaves `size == 2`, `evictions == 0`; `get("a") == 9`.
- R8 → `stats` returns a `CacheStats` instance; all fields are `int`; `stats.size` equals current entry count; mutating a returned snapshot raises (frozen) and does not affect later snapshots.
- R9 → fresh instance has `hits == misses == evictions == 0`; counters only increase across a sequence of operations; no API exposes a decrement or reset.
- R10 → structural: implementation uses `collections.OrderedDict` with `move_to_end` / `popitem(last=False)` (verified by code review, not a timing test).
- R11 → tuple and frozenset keys work; `get`/`put` with a `list` key raises `TypeError` (not caught by the class).
- R12 → `from tokenlab.cache import CacheStats, LruCache` succeeds; `CacheStats` is a frozen dataclass.

## 9. Open questions

None. All ticket §14 inferred assumptions are adopted as written (intake closed; per autopilot rules a non-URGENT CLARIFY to intake means "use the §14 inferred assumption and proceed"). The pipeline may advance.

**Tracked deliberate deviation (not an open question):** the class name `LruCache` deviates from CONSTITUTION §3 acronym-casing (which prescribes `LRUCache`). This is intentional — the name is a locked user requirement (ticket §1/§3) with stdlib precedent (`functools.lru_cache`) — and is recorded in §5.1 D9 and tracked as a **minor** in `BACKLOG.md` (`B-008`). Per CONSTITUTION §12.1, a minor stays in the backlog and does not block convergence. code-reviewer's REJECT on this point is **downgraded from major to minor** on this basis; no rename is performed.

## 10. Observability plan

### 8a — Operational events (always required)

`LruCache` is a pure in-memory utility with no business-meaningful state change, no actor, no resource ID, and no external boundary. Per CONSTITUTION §8a, structured event logging targets *business-meaningful* state changes that an auditor, support engineer, or PM would reconstruct after the fact. Cache get/put/evict are not such events — they are internal memoization mechanics local to a single process and instance. Emitting logs from a hot O(1) path would also violate the §8a "no printf in production paths" spirit and the R10 performance intent.

**Decision: no structured log events are required for normal cache operations**, confirming ticket §11. The table below documents the single deliberate operational concern (eviction) and why it is intentionally NOT logged, so `observability-auditor` can verify the spec→event mapping resolves to "none, by design".

| Spec ref | Event name (enum const) | Level | Key fields | Metric / Alert |
| --- | --- | --- | --- | --- |
| R6 eviction | _none — intentionally not logged_ | n/a | n/a | Eviction is exposed via `stats.evictions` (caller-pollable counter), not a log line. No process-global metric or alert: eviction is normal, expected, per-instance behavior, not a degradation. |
| R1 invalid capacity | _none — caller-facing exception_ | n/a | n/a | Surfaced as a `ValueError` to the caller at construction; the caller's own observability layer records it if relevant. Library does not own a logger. |

> §8b audit, §8c analytics, §8d security monitoring are all `[scope: disabled]` in CONSTITUTION §8 — tables omitted per template instructions.

## 10.1 Test execution requirements

Inherited from CONSTITUTION §4. No feature-specific exceptions.

- **Local isolation:** inherit §4.1 — none needed; tests are pure in-memory, no external infrastructure.
- **E2E policy:** inherit §4.3 — disabled; unit tests at `tests/unit/test_cache.py` are sufficient. No integration suite required (no external boundary to integrate against).
- **Coverage target:** inherit §4 — floor is 0% (tracked, not gated). Coverage is a smoke alarm; tests should cover every Rn acceptance criterion above regardless of the numeric floor.
- **TDD policy:** inherit §4.2 — spec-derived-post-impl; `test-engineer` writes tests from this spec after `developer`, citing the Rn numbers.
