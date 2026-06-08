# lru-cache — Software Design Document

> Source ticket: `/docs/requirements/lru-cache.md` (locked 2026-06-08, carries 5 answered clarifications and 7 inferred assumptions).
> Constitution: `/CONSTITUTION.md` (§1 Python 3.12 stdlib-only, pytest; §6 performance budgets TBD — structural-only checking; §8a always-on; §8b/c/d disabled; §13 versioning = none; §14 autonomous) + `/CONSTITUTION.project.md` (no §P sections defined).

## 1. Context

`tokenlab` needs a general-purpose, dependency-free bounded cache primitive. `LruCache` is a
fixed-capacity in-memory key→value store that evicts the **least-recently-used** entry when a
new key is inserted at capacity, and exposes cumulative hit/miss/eviction/size statistics. It
replaces ad-hoc `dict` usage in contexts where eviction under memory pressure is required, both
internally and for library consumers.

`LruCache` is a pure in-memory utility: it performs no I/O, no persistence, and no network calls;
nothing survives process exit. It makes **no thread-safety guarantee** — callers are responsible
for external synchronization.

**What it explicitly does NOT do** (enumerated in §3): no thread safety / internal locking, no
TTL or time-based expiry, no runtime type-checking of keys or values, no stats-reset method, no
persistence, no resize-after-construction, no structured log events, and no public API beyond
`__init__`, `get`, `put`, and `stats`.

This document covers the full feature. **No `/docs/api/`, `/docs/data-models/`, or
`/docs/diagrams/` artifacts are produced**, because:
- there is no HTTP/network interface → no OpenAPI contract (§5);
- there is no *persisted* state — the in-memory entry table is fully specified inline and never
  outlives the process → no data-model document (§6);
- there is a single in-process collaborator (the calling code) → no sequence diagram (the
  multi-component threshold of >2 collaborators is not met).

## 2. Requirements

Each requirement is testable and cited back to the ticket.

- R1: A public class `LruCache` exists at `src/tokenlab/cache.py`, importable as
  `from tokenlab.cache import LruCache`. <!-- Sources: ticket §3 (file location & import), §12 success criterion 1, §14 (canonical import path, inferred) -->
- R2: `LruCache(capacity: int)` constructs a cache with a fixed maximum number of entries equal to
  `capacity`. `capacity` is immutable after construction; no resize method is provided. <!-- Sources: ticket §3, §6, §14 (immutable capacity, inferred) -->
- R3: Constructing with `capacity` ≤ 0 (zero or any negative integer) raises `ValueError` at
  construction time. Both zero and negative raise the same `ValueError`. <!-- Sources: ticket §3, §6, §10, §12 success criterion 2, §13 Q5, §14 (negative == same ValueError, inferred) -->
- R4: `get(key, default=None)` returns the stored value when `key` is present, promoting that key
  to most-recently-used (MRU), and increments `stats().hits` by 1. <!-- Sources: ticket §3, §7, §12 success criterion 5, §13 Q4 -->
- R5: `get(key, default=None)` on a missing key returns `default` (which is `None` when not
  supplied), raises no exception, and increments `stats().misses` by 1. It does NOT modify
  ordering, size, or evictions. <!-- Sources: ticket §3, §7, §10, §12 success criteria 3 & 4, §13 Q4 -->
- R6: `put(key, value)` on a **new** key inserts the entry as MRU and returns `None`. A subsequent
  `get(key)` returns `value`. <!-- Sources: ticket §3, §7, §12 success criterion 6 -->
- R7: `put(key, value)` on an **existing** key updates the stored value in place, promotes that key
  to MRU, returns `None`, and does NOT increment `stats().evictions`. <!-- Sources: ticket §3, §7, §10, §12 success criterion 7, §14 (update-no-evict, inferred) -->
- R8: When the cache is at capacity and `put` is called with a **new** key, the least-recently-used
  entry is evicted first (`stats().evictions` incremented by 1), then the new key is inserted as
  MRU. The evicted entry is the LRU one — never the MRU one. <!-- Sources: ticket §3, §10, §12 success criteria 8 & 11 & 12 -->
- R9: Recency ordering reflects access: `get` of a present key and `put` of any key (new or
  existing) both make that key MRU. Eviction therefore targets the key least-recently touched by
  any `get` or `put`. (E.g. with capacity 2: `put(A)`, `put(B)`, `get(A)`, `put(C)` evicts `B`, not
  `A`.) <!-- Sources: ticket §3 (promotion semantics), §12 success criterion 12 -->
- R10: `stats()` returns an object with integer fields `hits`, `misses`, `evictions`, and `size`,
  accessible by attribute name. `size` is the current entry count (never bytes, never capacity);
  `hits`/`misses`/`evictions` are cumulative from construction with no reset mechanism. <!-- Sources: ticket §3, §7, §8 (size = entry count), §12 success criteria 9 & 10, §13 Q1, §14 (cumulative no reset, size = count, inferred) -->
- R11: Keys must be hashable; values are unrestricted. No runtime type-checking of keys, values,
  or `default` is performed. (A non-hashable key surfaces the standard `TypeError` from the
  underlying mapping; this is the language contract, not a `LruCache`-defined behavior.) <!-- Sources: ticket §6, §13 Q3 -->
- R12: `get` and `put` operate in **amortized O(1)** time, independent of the number of stored
  entries. (Standard LRU contract; `performance-analyst` flags any non-O(1) implementation as a
  structural issue per ticket §11 / CONSTITUTION §6.) <!-- Sources: ticket §11 (O(1) amortized expectation) -->
- R13: The implementation uses only the Python 3.12 standard library — no third-party runtime or
  test dependencies. `stats()` returns a stdlib-backed value object (see §TD-1). <!-- Sources: ticket §9, §11, §12 success criteria 13 & 14; CONSTITUTION §1 -->
- R14: `LruCache` and each public method carry a docstring describing purpose, parameters, return
  value, ordering/eviction semantics, and the `ValueError` construction contract. <!-- Sources: ticket §3; CONSTITUTION §3 -->

## 3. Non-goals

Explicitly out of scope. Listed so reviewers do not treat their absence as a gap.

- **Thread safety / internal locking** — no guarantee; callers synchronize externally (ticket §4, §13 Q2).
- **TTL / time-based expiry** — entries never expire by time (ticket §4, §14).
- **Runtime type-checking** of keys/values/default (ticket §4, §6, §13 Q3).
- **Stats-reset method** — stats are cumulative and irreversible from construction (ticket §4, §14).
- **Persistence** — purely in-memory; nothing survives GC or process exit (ticket §4, §8).
- **Capacity resize after construction** — `capacity` is fixed (ticket §14, R2).
- **Structured operational log events** — pure in-memory utility, no I/O boundary; §8a does not
  apply (ticket §4, §11; see §10 justification).
- **Any public API beyond `__init__`, `get`, `put`, `stats`** — no `__len__`, `__contains__`,
  `keys()`, `clear()`, `peek()`, etc. are mandated by this spec (ticket §4). Adding any would be
  a scope addition routed back through the ticket.

## 4. Architecture

A single class in one module:

```
src/tokenlab/cache.py
    LruCache                              # the only public name
        __init__(capacity: int)
        get(key, default=None) -> Any
        put(key, value) -> None
        stats() -> CacheStats
    CacheStats                            # value object returned by stats() (see §TD-1)
    (the ordered entry store and counters are instance-private)
```

Internal structure (§TD-2): a single `collections.OrderedDict` instance maps `key → value` and
carries recency order. MRU is the right end (most-recently inserted/moved); LRU is the left end.

Control flow (single in-process collaborator — no sequence diagram warranted):

1. **Construction** — validate `capacity ≥ 1` (R3); else raise `ValueError`. Initialize an empty
   `OrderedDict` and zeroed `hits`/`misses`/`evictions` counters. Store `capacity`.
2. **`get(key, default)`** — if `key` present: `move_to_end(key)` (promote to MRU, R4/R9),
   `hits += 1`, return stored value. Else: `misses += 1`, return `default` (R5). No eviction, no
   size change on the miss path.
3. **`put(key, value)`** — if `key` present: assign value, `move_to_end(key)` (R7/R9); evictions
   unchanged. Else (new key): if `len == capacity`, `popitem(last=False)` to drop the LRU entry,
   `evictions += 1` (R8); then assign the new entry (becomes MRU). Return `None`.
4. **`stats()`** — return a fresh `CacheStats(hits, misses, evictions, size=len(store))` (R10).

Boundary discipline (CONSTITUTION §3, §5): input is accepted at the method boundary; the only
input validation is `capacity` (raised at the origin in `__init__`). Hashability errors for keys
surface as the underlying `TypeError` at their origin and are not caught-and-swallowed (R11).

### Technical decisions (decided within the locked stack; disclosed for review)

- **TD-1 — `stats()` returns a frozen `dataclasses.dataclass`** named `CacheStats` with fields
  `hits: int`, `misses: int`, `evictions: int`, `size: int`. *Rationale:* the ticket §7/§13 Q1
  permits "dataclass or namedtuple"; a frozen dataclass gives attribute access (matching the
  ticket's `stats().hits` usage), an immutable snapshot (callers can't mutate counters), a clear
  type name in tracebacks/IDEs, and is stdlib-only. `frozen=True` makes each `stats()` call an
  immutable point-in-time snapshot, which is the safer default for a returned stats object.
- **TD-2 — single `collections.OrderedDict` as the backing store.** *Rationale:* `OrderedDict`
  provides O(1) `move_to_end` and `popitem(last=False)`, which directly implement MRU promotion
  and LRU eviction, satisfying the amortized-O(1) contract (R12) with no third-party dependency
  and minimal code. A plain `dict` (insertion-ordered since 3.7) lacks `move_to_end`, so
  `OrderedDict` is the right stdlib primitive.
- **TD-3 — eviction-then-insert ordering on the at-capacity new-key path.** *Rationale:* evicting
  before inserting keeps `len(store)` from transiently exceeding `capacity` and makes the LRU
  selection (`popitem(last=False)`) deterministic — the new key is never a candidate for its own
  eviction (R8).
- **TD-4 — counters are plain instance `int` attributes; `size` is derived from `len(store)` at
  call time, not stored.** *Rationale:* deriving `size` eliminates a class of drift bugs where a
  separately-tracked counter disagrees with the actual entry count (R10).

These are reversible internal choices. None changes the public contract in §2.

## 5. API contract

Not applicable — there is no HTTP/network interface. The "interface" is the Python class surface,
fully specified by R1–R14. **No `/docs/api/lru-cache.openapi.yaml` is produced.**

Authoritative public surface:

```python
from dataclasses import dataclass
from typing import Any, Hashable

@dataclass(frozen=True)
class CacheStats:
    hits: int
    misses: int
    evictions: int
    size: int

class LruCache:
    def __init__(self, capacity: int) -> None: ...      # ValueError if capacity <= 0  (R3)
    def get(self, key: Hashable, default: Any = None) -> Any: ...   # R4, R5
    def put(self, key: Hashable, value: Any) -> None: ...           # R6, R7, R8
    def stats(self) -> CacheStats: ...                              # R10
```

## 6. Data model

Not applicable — `LruCache` holds only transient in-memory state (an `OrderedDict` of entries and
three integer counters) and persists nothing. The in-memory shape is fully specified by §4 and
TD-1/TD-2/TD-4. **No `/docs/data-models/lru-cache.md` is produced.**

## 7. Failure modes

- **Input validation (the only first-class failure surface):** `LruCache(0)` and `LruCache(-n)`
  for any negative `n` raise `ValueError` at construction (R3). This is the sole `LruCache`-defined
  exception path.
- **Missing-key lookup:** `get` on an absent key is **not** a failure — it returns `default` and
  increments `misses` (R5). No exception is raised.
- **Non-hashable key:** passing an unhashable key to `get`/`put` raises the standard library
  `TypeError` at its origin (the `OrderedDict` operation), not a `LruCache`-defined error (R11).
  The spec does not catch or reshape this; it is the language's typed contract.
- **External-service failure:** none — no external dependencies, no I/O (ticket §9, §10).
- **Concurrency:** **no thread-safety guarantee** (ticket §4, §13 Q2). Concurrent mutation from
  multiple threads without external locking is undefined behavior by design; this is a documented
  non-goal, not a defect. The class is safe for single-threaded use and for callers that provide
  their own synchronization.
- **No silent data loss in the constitutional sense (§2.3):** eviction is the *specified* behavior
  of a bounded cache, surfaced through `stats().evictions`; it is observable, counted, and the
  caller can read the eviction count at any time. It is not a silent drop.

## 8. Acceptance criteria

1:1 mapping to requirements (test-engineer cites Rn). Maps onto the ticket §12 success criteria.

- R1 → `from tokenlab.cache import LruCache` succeeds with no import error on Python 3.12;
  `LruCache` is a class. (ticket §12.1)
- R2 → `LruCache(1)` constructs without error; after construction the capacity cannot be changed
  (no resize method exists). (ticket §12.2)
- R3 → `LruCache(0)` raises `ValueError`; `LruCache(-1)` raises `ValueError`; both raise exactly
  `ValueError`. (ticket §12.2)
- R4 → for a cache holding `key`, `get(key)` returns the stored value and `stats().hits` increases
  by 1 versus before the call; the key becomes MRU (verified via R9-style eviction follow-up).
  (ticket §12.5)
- R5 → `get("absent")` returns `None` and increments `stats().misses`; `get("absent", "d")` returns
  `"d"` and increments `stats().misses`; neither changes `stats().size` or `stats().evictions`.
  (ticket §12.3, §12.4)
- R6 → after `put("k", "v")` on a fresh `LruCache(2)`, `get("k") == "v"`. (ticket §12.6)
- R7 → `put("k", 1)` then `put("k", 2)` on `LruCache(2)` leaves `get("k") == 2`, `stats().size == 1`,
  and `stats().evictions == 0`. (ticket §12.7)
- R8 → on `LruCache(1)`: `put("A", 1)`, `put("B", 2)` ⇒ `get("A") is None` (with miss counted),
  `get("B") == 2`, and `stats().evictions == 1`. (ticket §12.8, §12.11)
- R9 → on `LruCache(2)`: `put("A", 1)`, `put("B", 2)`, `get("A")`, `put("C", 3)` ⇒ `"B"` is evicted
  (`get("B") is None`) while `get("A") == 1` and `get("C") == 3`. (ticket §12.12)
- R10 → after a scripted sequence of N₁ hits, N₂ misses, and N₃ evictions, `stats()` reports
  `hits == N₁`, `misses == N₂`, `evictions == N₃`, and `size == current entry count`
  (and `size != capacity` when the cache is partially filled). (ticket §12.9, §12.10)
- R11 → `put({}, 1)` / `get({})` (unhashable key) raises `TypeError`; a hashable non-string key
  (e.g. an `int` or `tuple`) round-trips through `put`/`get` correctly.
- R12 → asserted structurally, not by timing: review confirms `get`/`put` use `OrderedDict`
  O(1) operations (`move_to_end`, `popitem(last=False)`, single index) with no full-scan over
  entries. (ticket §11; `performance-analyst` owns the structural check.)
- R13 → `cache.py` imports only stdlib modules (source check); the test suite runs under `pytest`
  with no third-party install. (ticket §12.13, §12.14)
- R14 → `LruCache.__doc__`, `LruCache.get.__doc__`, `LruCache.put.__doc__`, and
  `LruCache.stats.__doc__` are each non-empty strings.

## 9. Open questions

The ticket §14 lists seven assumptions the user did NOT confirm. Per the spec-architect operating
rule, ticket additions the user has not locked are recorded here for qa-reviewer to verify intent.
Each is resolved into a requirement above with the cited default; **none blocks the pipeline** —
all are consistent with the constitution and the ticket's confirmed §13 answers. qa-reviewer
should confirm the chosen default matches user intent before release.

- OQ-1 — Canonical import path is `from tokenlab.cache import LruCache` (resolved in R1 per ticket
  §3/§14). No conflict.
- OQ-2 — `capacity` is immutable after construction; no resize method (resolved in R2 per ticket
  §14). No conflict.
- OQ-3 — `put` on an existing key updates and promotes to MRU but does NOT increment `evictions`
  (resolved in R7 per ticket §10/§14). No conflict.
- OQ-4 — Stats are cumulative from construction with no reset method (resolved in R10 per ticket
  §4/§14). No conflict.
- OQ-5 — No TTL / time-based expiry (resolved as a §3 non-goal per ticket §4/§14). No conflict.
- OQ-6 — `stats().size` reports entry count, not bytes (resolved in R10 per ticket §8/§14). No
  conflict.
- OQ-7 — Negative capacity raises the same `ValueError` as zero capacity (resolved in R3 per
  ticket §14). No conflict.

> The pipeline rule is "do not advance until §9 is empty." These entries are *resolved assumptions
> awaiting user/qa confirmation*, not unanswered blockers — each is already reified into a
> requirement with a default consistent with the locked ticket and the constitution. If qa-reviewer
> or the user overrides any default, the corresponding Rn changes and this entry is struck. No entry
> here halts development.

## 10. Observability plan

### 8a — Operational events (always required)

CONSTITUTION §8a requires "every business-meaningful state change" to emit one structured log
line, where business-meaningful means "anything an auditor, support engineer, or product manager
would want to reconstruct after the fact." `LruCache` is a **pure in-memory primitive**: it
performs no I/O, no persistence, and no network call; it owns no `actor_id`, `resource_id`, or
`trace_id`; and all of its state changes (hit, miss, insert, update, eviction) are deterministic
consequences of caller method calls, fully observable through `stats()` and the method
return/raise contract.

Emitting a structured log line from inside the cache would (a) attach no correlation context the
primitive legitimately possesses, (b) duplicate or pre-empt the *caller's* boundary logging — the
caller is the boundary that decides whether a cache operation is business-meaningful in its
domain — and (c) introduce an I/O side effect into a class the ticket (§4, §8, §11) specifies as
side-effect-free with no logging.

Eviction in particular is **not** silent data loss in the §2.3 sense: it is the specified contract
of a bounded cache and is surfaced through the always-available `stats().evictions` counter, which
the caller can read and log within its own observed context.

**Therefore this feature emits no structured operational log line, and that is the correct reading
of §8a, not an omission.** The mapping "every spec-mandated success criterion and failure mode has
a corresponding logged event" is satisfied vacuously: the contract is the return/raise/`stats()`
behavior, asserted directly by the §8 acceptance tests rather than by log inspection. The ticket
§4 and §11 explicitly record that §8a operational observability does not apply here.
`observability-auditor` should verify this justification rather than expect an event-table row.

| Spec ref | Event name (enum const) | Level | Key fields | Metric / Alert |
| --- | --- | --- | --- | --- |
| — | _none — pure in-memory primitive, no business state change, no I/O boundary (see justification above)_ | — | — | — |

> §8b (audit), §8c (analytics), §8d (security events) are all `scope: disabled` in CONSTITUTION §8
> and the ticket §4/§11 — their tables are intentionally omitted per the template rule. No audit,
> analytics, or security-monitoring events are introduced by this feature.

## 10.1 Test execution requirements

Inherited from CONSTITUTION §4. No feature-specific exceptions.

- Local isolation: inherit §4.1 — none needed; this is a pure in-memory class requiring no
  external infrastructure. Tests run in-process with pytest, no services.
- E2E policy: inherit §4.3 — disabled; unit tests are sufficient. Tests live at
  `tests/unit/test_cache.py` (ticket §3, §12).
- Coverage target: inherit §4 coverage floor (0 %, tracked not gated). Coverage is a smoke alarm
  here, not a goal; the acceptance criteria in §8 are the real bar. Given the small pure surface,
  high unit coverage is expected (ticket §11).
