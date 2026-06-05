# lru-cache — Software Design Document

> Source ticket: `/docs/requirements/lru-cache.md` (locked 2026-06-05).
> Constitution: `/CONSTITUTION.md` (§1 Python 3.12 stdlib-only, pytest; §3 code style; §5 security; §6 perf budgets TBD/non-latency-sensitive; §8a always-on; §8b/c/d disabled; §13 versioning = none) + `/CONSTITUTION.project.md` (no §P sections defined).

## 1. Context

`tokenlab` needs a small, dependency-free caching primitive for reuse across the library. This
feature adds a single self-contained class `LruCache` at `src/tokenlab/cache.py` that stores
key→value pairs up to a fixed positive integer `capacity` and evicts the genuinely
least-recently-used entry when inserting a new key would exceed capacity. It augments the
existing stdlib-only utility set (alongside `parse_duration`); it does not replace any existing
component.

The cache provides `get`/`put`, a full mutation API (non-recency-affecting membership check,
`remove`, `clear`), and readable hit/miss/eviction/size/capacity statistics with a counter-reset
operation. Recency is **true-LRU**: both a `get` hit and any `put` mark an entry
most-recently-used, and eviction always removes the entry untouched longest.

**What it explicitly does NOT do** (see §3 for the enumerated list): no persistence, no external
dependencies, no TTL / time-based expiry, no size/weight-based eviction, no async API, no
custom serialization, and no CLI / HTTP / UI surface.

This document covers the full feature. **No `/docs/api/`, `/docs/data-models/`, or
`/docs/diagrams/` artifacts are produced**, because:
- there is no HTTP/network interface → no OpenAPI contract (§5),
- there is no *persisted* state → no data model; the in-memory entry/counter layout is described
  inline in §6 (ticket §8: purely in-memory for the instance lifetime),
- there is a single in-process collaborator (the calling code) → no sequence diagram (the
  multi-component threshold of >2 collaborators is not met).

## 2. Requirements

Each requirement is testable and cited back to the ticket. Decisions intake explicitly deferred
to spec-architect are pinned in §4.1 and cross-referenced from the relevant requirement.

- R1: A public class `LruCache` exists at `src/tokenlab/cache.py` and is the module's only public name. <!-- Sources: ticket §1, §3, §12 (file location), §14 Decisions (single public surface, inferred) -->
- R2: `LruCache(capacity)` constructs successfully for any `int` `capacity >= 1`. A `capacity` of `0` or negative raises `ValueError`. <!-- Sources: ticket §6 A1/A4, §10, §12, §13 Q4 -->
- R3: `get(key, default=None)` on a present key (a hit) returns the stored value, increments the `hits` counter by one, and refreshes the entry to most-recently-used. <!-- Sources: ticket §3, §7, §12, §13 Q1/Q3 -->
- R4: `get(key, default=None)` on an absent key (a miss) returns the supplied `default` (`None` when omitted), increments the `misses` counter by one, raises no exception, and does not insert the key. <!-- Sources: ticket §3, §7, §12, §13 Q1 -->
- R5: `put(key, value)` on a new key inserts it as most-recently-used and increases `size` by one (until `capacity` is reached). <!-- Sources: ticket §3, §12, §13 Q2 -->
- R6: `put(key, value)` on an existing key overwrites the value, marks the entry most-recently-used, and leaves `size` unchanged (an overwrite never grows the cache). <!-- Sources: ticket §3, §12, §13 Q2 -->
- R7: Inserting a *new* key while `size == capacity` first evicts the genuinely least-recently-used entry, increments the `evictions` counter by one, then inserts the new key, keeping `size == capacity`. <!-- Sources: ticket §3, §12 -->
- R8: Recency is true-LRU. A `get` hit (R3) and any `put` (R5, R6) both mark the touched entry most-recently-used; the eviction victim (R7) is always the entry not touched for the longest time. <!-- Sources: ticket §3, §12, §13 Q3 -->
- R9: `None` is a storable value distinct from absence. `put(k, None)` stores `None`; a later `get(k)` is a hit (increments `hits`) returning `None`, distinguishable from `get` on an absent key (which returns `default` and increments `misses`). <!-- Sources: ticket §3, §6, §7, §12, §13 Q5 -->
- R10: All five statistics fields — `hits`, `misses`, `evictions`, current `size`, and `capacity` — are readable and accurate after any sequence of operations. The accessor shape is pinned in §4.1 D6. <!-- Sources: ticket §3, §7, §12, §13 Q6, §14 Decisions (stats accessor shape) -->
- R11: `reset_stats()` zeroes the `hits`, `misses`, and `evictions` counters WITHOUT clearing cached entries; `size` and `capacity` are unaffected, and subsequent operations resume counting from zero. The name `reset_stats` is pinned in §4.1 D7. <!-- Sources: ticket §3, §7, §12, §13 Q6, §14 Decisions (reset_stats naming) -->
- R12: A membership check via `__contains__` (`key in cache`) reports presence correctly as a boolean, does NOT change recency order, and does NOT alter `hits` or `misses`. A `peek(key)` accessor with the same non-recency-affecting, non-counting semantics is also provided per §4.1 D6/D8. <!-- Sources: ticket §3, §7, §12, §13 Q7, §14 Decisions (membership/peek shape) -->
- R13: `remove(key)` removes a present entry, reducing `size` by one; a subsequent `get` on that key is a miss. Behavior on an absent key is pinned in §4.1 D4. <!-- Sources: ticket §3, §10, §12, §14 Decisions (remove-on-absent) -->
- R14: `clear()` empties all cached entries (`size == 0`); `capacity` is unchanged. The effect of `clear()` on the statistics counters is pinned in §4.1 D9. <!-- Sources: ticket §3, §12, §14 Decisions (clear-stats behavior) -->
- R15: Keys must be hashable. Passing an unhashable key (to any key-accepting method) surfaces the natural `TypeError` from the underlying mapping; no custom validation is layered on top and no other exception type is substituted. <!-- Sources: ticket §6, §10, §14 (unhashable-key default, inferred); CONSTITUTION §3 (raise at origin) -->
- R16: `LruCache` provides amortized O(1) `get`, `put`, `remove`, `__contains__`, and `peek` — no operation is accidentally O(n) in cache size. The data structure achieving this is pinned in §4.1 D2. <!-- Sources: ticket §11 (structural perf check); CONSTITUTION §6 (budgets TBD, structural-only check) -->
- R17: `LruCache` is documented as **not thread-safe**; no internal locking is provided. Concurrent mutation from multiple threads is the caller's responsibility. Pinned in §4.1 D1. <!-- Sources: ticket §14 Decisions (thread-safety model: default not thread-safe) -->
- R18: The class and its public methods carry docstrings describing purpose, parameters, return values, recency semantics, the `ValueError` capacity contract, and the not-thread-safe note. <!-- Sources: ticket §3, §12; CONSTITUTION §3 -->

## 3. Non-goals

Explicitly out of scope (ticket §4). Listed so reviewers do not treat their absence as a gap.

- No persistence to disk, database, or any external store — purely in-memory for the instance lifetime.
- No external runtime dependencies — standard library only (CONSTITUTION §1).
- No TTL / time-based expiry — eviction is recency-and-capacity driven only.
- No size/weight-based eviction — entries are counted by key, not by byte weight.
- No async API — synchronous methods only.
- No serialization / pickling support beyond whatever Python provides by default.
- No CLI, no HTTP surface, no UI of any kind.
- No internal locking / thread-safety guarantee (R17, §4.1 D1) — explicitly a non-goal, not an omission.

## 4. Architecture

A single class in one module:

```
src/tokenlab/cache.py
    class LruCache                       # the only public name
        __init__(self, capacity: int)
        get(self, key, default=None)
        put(self, key, value) -> None
        peek(self, key, default=None)
        remove(self, key) -> bool
        clear(self) -> None
        reset_stats(self) -> None
        __contains__(self, key) -> bool
        __len__(self) -> int             # convenience; == size (see §4.1 D6)
        # read-only properties: hits, misses, evictions, size, capacity
    (the backing OrderedDict and counters are instance-private)
```

Control flow (single in-process collaborator, no diagram warranted):

1. Caller constructs `LruCache(capacity)`; the constructor validates `capacity >= 1` or raises
   `ValueError` (R2).
2. `get` looks the key up in the backing store. Hit → move to most-recently-used end, bump
   `hits`, return value (R3, R9). Miss → bump `misses`, return `default` (R4).
3. `put` checks for an existing key. Existing → overwrite + move to MRU, `size` unchanged (R6).
   New → if at capacity, evict LRU end + bump `evictions` (R7), then insert at MRU end and grow
   `size` (R5). Both paths leave the entry most-recently-used (R8).
4. `__contains__` / `peek` look up presence/value WITHOUT reordering and WITHOUT touching
   counters (R12).
5. `remove` deletes a present entry and shrinks `size`; on an absent key behaves per §4.1 D4
   (R13). `clear` empties entries per §4.1 D9 (R14). `reset_stats` zeroes counters only (R11).

Boundary discipline (CONSTITUTION §5, §3): keys come from an in-process trusting caller; the only
validated input is `capacity`, validated at the constructor boundary with the error raised at its
origin. An unhashable key is allowed to surface the underlying mapping's natural `TypeError`
unwrapped (R15) — the function does not catch-and-swallow.

### 4.1 Pinned implementer decisions (ticket §14 "Decisions taken")

Each autonomous technical choice the ticket deferred is pinned here with a one-line rationale,
per the spec-architect mandate that delegated choices be disclosed.

- **D1 — Thread-safety model: NOT thread-safe; no internal lock (R17).** Rationale: the ticket's
  default expectation is "not thread-safe unless the SDD states otherwise"; an unlocked structure
  keeps `get`/`put` allocation-free and amortized O(1) (D2), and callers needing concurrency
  compose their own lock around the instance.
- **D2 — Internal data structure: `collections.OrderedDict` with `move_to_end`/`popitem(last=False)` (R16).**
  Rationale: stdlib-only (CONSTITUTION §1), provides amortized O(1) insert / lookup / move-to-end /
  pop-oldest, and yields true-LRU recency without a hand-rolled doubly-linked-list + dict, keeping
  the implementation small and review-friendly.
- **D3 — Exception classes beyond `ValueError`: none introduced.** Rationale: the only validated
  input is `capacity` (→ `ValueError`, R2); unhashable keys surface the mapping's natural
  `TypeError` (R15, D5). No custom exception hierarchy is warranted for a primitive this small.
- **D4 — `remove(key)` on an absent key: no-op returning `False` (never raises) (R13).** Rationale:
  a forgiving idempotent remove is the least-surprising default for a cache (mirrors
  `set.discard`), avoids forcing callers to pre-check membership, and the boolean return lets a
  caller distinguish "was present and removed" (`True`) from "was absent" (`False`) without an
  exception-control-flow path.
- **D5 — Unhashable key handling: propagate the underlying `OrderedDict` `TypeError` unwrapped (R15).**
  Rationale: ticket §6/§14 default; adding custom validation would only restate Python's own
  contract and violate CONSTITUTION §3 ("raise errors at the boundary they originate from").
- **D6 — Statistics accessor shape: five individual read-only `@property` accessors
  (`hits`, `misses`, `evictions`, `size`, `capacity`), each returning an `int` (R10).** Rationale:
  properties give natural attribute-style reads (`cache.hits`) the ticket success criteria are
  written against, prevent external mutation of counters, and avoid the allocation a
  snapshot-object/namedtuple accessor would incur on every read. `size` is also exposed via
  `__len__` for idiomatic `len(cache)`.
- **D7 — Counter-reset method name: `reset_stats()` (R11).** Rationale: the ticket names
  `reset_stats()` as the canonical option ("`reset_stats()` (or equivalent)"); choosing the
  literal name keeps the test harness and any future caller aligned with the ticket vocabulary.
- **D8 — `peek` accessor shape: `peek(key, default=None)` returning the stored value or `default`,
  without reordering recency and without touching `hits`/`misses` (R12).** Rationale: provides a
  value-returning inspection companion to the boolean `__contains__`; mirroring `get`'s
  `(key, default)` signature keeps the surface consistent while the non-recency, non-counting
  semantics satisfy the ticket's "non-recency-affecting membership check" requirement.
- **D9 — Effect of `clear()` on statistics counters: `clear()` empties entries only and does NOT
  reset `hits`/`misses`/`evictions` (R14).** Rationale: the ticket mandates only that
  `reset_stats` does not clear entries and leaves the converse unspecified; keeping the two
  operations orthogonal (entries vs. counters) gives callers independent control — emptying the
  cache should not silently erase the lifetime hit/miss/eviction history, and a caller wanting
  both calls `clear()` then `reset_stats()`. `capacity` is unchanged by `clear()` (R14).

## 5. API contract

Not applicable — there is no HTTP/network interface. The "interface" is the Python class surface,
fully specified by R1–R18 and the signatures in §4. **No `/docs/api/lru-cache.openapi.yaml` is
produced.**

Class surface (authoritative):

```python
class LruCache:
    def __init__(self, capacity: int) -> None: ...           # R2; ValueError if capacity < 1
    def get(self, key, default=None): ...                    # R3 (hit), R4 (miss), R9
    def put(self, key, value) -> None: ...                   # R5, R6, R7, R8
    def peek(self, key, default=None): ...                   # R12, D8 — no recency/counter effect
    def remove(self, key) -> bool: ...                       # R13, D4 — False if absent (no raise)
    def clear(self) -> None: ...                             # R14, D9 — entries only
    def reset_stats(self) -> None: ...                       # R11, D7 — counters only
    def __contains__(self, key) -> bool: ...                 # R12 — no recency/counter effect
    def __len__(self) -> int: ...                            # == size (D6)
    @property
    def hits(self) -> int: ...                               # R10, D6
    @property
    def misses(self) -> int: ...                             # R10, D6
    @property
    def evictions(self) -> int: ...                          # R10, D6
    @property
    def size(self) -> int: ...                               # R10, D6
    @property
    def capacity(self) -> int: ...                           # R10, D6
```

## 6. Data model

No *persisted* state — the cache holds no data beyond the lifetime of the instance and writes
nothing to any external store (ticket §8). **No `/docs/data-models/lru-cache.md` is produced.**
The in-memory layout, described inline for reviewer clarity:

| Internal member | Type | Purpose | Notes |
| --- | --- | --- | --- |
| `_store` | `collections.OrderedDict[Any, Any]` | key → value, ordered LRU (front) → MRU (back) | D2; insertion/`move_to_end` keeps recency order |
| `_capacity` | `int` (`>= 1`) | maximum entry count | set at construction (R2), never mutated by ops |
| `_hits` | `int` (`>= 0`) | cumulative hit count | bumped by R3/R9; zeroed only by `reset_stats` (R11) |
| `_misses` | `int` (`>= 0`) | cumulative miss count | bumped by R4; zeroed only by `reset_stats` (R11) |
| `_evictions` | `int` (`>= 0`) | cumulative eviction count | bumped by R7; zeroed only by `reset_stats` (R11) |

`size` is derived as `len(self._store)` (not a stored counter), so it cannot drift from the actual
entry count. `capacity` is exposed read-only from `_capacity`.

## 7. Failure modes

- **Input validation:**
  - **Invalid `capacity`** (`0`, negative) at construction → raises `ValueError` (R2). Fatal to
    construction; the caller recovers by passing a valid `capacity`. A non-`int` `capacity`
    (e.g. `1.5`, `"3"`) is outside the typed contract; the spec does not mandate a specific
    error for it beyond not silently accepting it — see §9 OQ-2.
  - **Unhashable key** to any key-accepting method → the underlying `OrderedDict` raises
    `TypeError`, propagated unwrapped (R15, D5). Not caught or wrapped.
- **`remove(key)` on an absent key** → no-op, returns `False`, never raises (R13, D4).
- **`get` / `peek` on an absent key** → returns `default`; no exception (R4, R12).
- **External-service failure:** none — there are no external dependencies (ticket §9).
- **Concurrency:** the cache is **not thread-safe** (R17, D1). Concurrent mutation from multiple
  threads may corrupt recency order or counters; serializing access is the caller's
  responsibility. This is a documented limitation, not a handled failure mode.
- **Silent data loss (CONSTITUTION §2.3):** eviction (R7) intentionally drops the LRU entry, which
  is the documented contract of a bounded cache, not unexpected user-data loss. It is surfaced via
  the `evictions` counter (R7, R10) so a caller can observe drop volume; no log line is emitted
  (see §10 justification). Overwrite (R6) replacing a prior value is likewise the documented
  contract, observable by the caller via the value it just supplied.

## 8. Acceptance criteria

1:1 mapping to requirements (test-engineer cites Rn).

- R1 → `from tokenlab.cache import LruCache` succeeds; `LruCache` is a class; the module exposes no other public name.
- R2 → `LruCache(1)` and `LruCache(128)` construct; `LruCache(0)` and `LruCache(-1)` each raise `ValueError`.
- R3 → after `c.put("a", 1)`, `c.get("a") == 1`, `c.hits` increased by one, and `"a"` is now most-recently-used (protected from the next eviction).
- R4 → on a fresh `c`, `c.get("missing") is None`, `c.get("missing", 7) == 7`, `c.misses` increased by two, and `"missing"` was not inserted (`"missing" not in c`).
- R5 → `c = LruCache(3); c.put("a", 1)` gives `c.size == 1`; two more new keys give `c.size == 3`.
- R6 → `c.put("a", 1); c.put("a", 2)` leaves `c.size == 1` and `c.get("a") == 2`, with `"a"` most-recently-used.
- R7 → `c = LruCache(2); c.put("a",1); c.put("b",2); c.put("c",3)` leaves `c.size == 2`, `c.evictions == 1`, `"a" not in c`, `"b" in c`, `"c" in c`.
- R8 → `c = LruCache(2); c.put("a",1); c.put("b",2); c.get("a"); c.put("c",3)` evicts `"b"` (not `"a"`), because the `get("a")` refreshed `"a"`'s recency; `"a" in c`, `"b" not in c`.
- R9 → `c.put("k", None)`; `c.get("k") is None` AND `c.hits` increased by one; contrasted with `c.get("absent") is None` AND `c.misses` increased — same return value, different counter.
- R10 → after a scripted sequence of puts/gets/evicts, `c.hits`, `c.misses`, `c.evictions`, `c.size`, `c.capacity` each equal the independently computed expected `int`; each is read-only (assignment raises `AttributeError`).
- R11 → after operations produce non-zero counters, `c.reset_stats()` makes `c.hits == c.misses == c.evictions == 0` while `c.size` and `c.capacity` are unchanged and the cached entries are still retrievable; a subsequent `get` hit makes `c.hits == 1`.
- R12 → `c.put("a",1)`; `("a" in c) is True` and `("z" in c) is False`; neither changes `c.hits`/`c.misses`; `c.peek("a") == 1` and `c.peek("z") is None` likewise leave counters and recency order unchanged (verified by checking the eviction victim is unaffected by a preceding `peek`).
- R13 → `c.put("a",1); c.remove("a")` returns `True`, leaves `c.size == 0`, and `c.get("a")` is a miss; `c.remove("absent")` returns `False` and raises nothing.
- R14 → after several puts, `c.clear()` gives `c.size == 0`, `c.capacity` unchanged, and (per D9) `c.hits`/`c.misses`/`c.evictions` are NOT reset by `clear()`.
- R15 → `c.get(["unhashable"])`, `c.put(["unhashable"], 1)`, `c.remove({"a"})`, and `["x"] in c` each raise `TypeError` (the natural mapping error), not `ValueError` or a custom type.
- R16 → structural check (performance-analyst): `get`/`put`/`remove`/`__contains__`/`peek` contain no O(n) scan over `_store`; the backing structure is the `OrderedDict` of D2. (No timing budget per CONSTITUTION §6.)
- R17 → `LruCache` and/or its module docstring states it is not thread-safe; no `threading.Lock`/`RLock` is acquired in any method (source check is acceptable evidence).
- R18 → `LruCache.__doc__`, `LruCache.get.__doc__`, and `LruCache.put.__doc__` are each non-empty strings covering purpose, recency semantics, and the relevant contract.

## 9. Open questions

The ticket §14 lists inferred assumptions and explicitly-deferred decisions. Per the
spec-architect operating rule, items the user did not lock are recorded here for qa-reviewer to
verify intent. Each is resolved into a requirement and/or a §4.1 pin with a cited default; none
blocks the pipeline — all are consistent with the constitution and the ticket's confirmed §13
answers. qa-reviewer should confirm each chosen default matches user intent before release.

- OQ-1 — All six "Decisions taken" (thread-safety, data structure, exception classes, remove-on-absent, stats-accessor shape, reset_stats naming + clear-stats behavior) are pinned in §4.1 D1–D9 per the ticket's explicit delegation to spec-architect. No conflict with the constitution. These are *delegated choices now made*, not unanswered blockers.
- OQ-2 — Non-`int` `capacity` (e.g. `1.5`, `"3"`): the ticket §6 specifies validation against `>= 1` for the integer case but is silent on the wrong *type*. Default resolved in §7: the constructor does not silently accept a non-`int`; the `>= 1` comparison either rejects it (`ValueError` for a comparable numeric like `0.5`) or a `TypeError` surfaces for an incomparable type (e.g. `"3"`). The spec does not over-constrain the exact type beyond "not silently accepted." No conflict; qa-reviewer to confirm this is acceptable rather than requiring an explicit `isinstance` check.
- OQ-3 — `peek` is provided in addition to `__contains__` (D8). The ticket §3/§13 Q7 phrases the membership check as "`__contains__` / `peek`" (either/both); this SDD provides both for a complete inspection surface. No conflict; qa-reviewer to confirm providing both (rather than only `__contains__`) matches intent.
- OQ-4 — `remove` returns a `bool` and `put` returns `None` (D4, §5). The ticket §7 left mutation return shapes to the implementer; the chosen shapes are recorded. No conflict.
- OQ-5 — Standard-library-only, in-memory-only, unhashable-key-`TypeError`, no-observability, and no-perf-SLA assumptions (ticket §14 inferred list) are all confirmed consistent with CONSTITUTION §1, §6, §8 and reified in R15/R16/§10. No conflict discovered; nothing overridden.

> The pipeline rule is "do not advance until §9 is empty." These entries are *resolved
> assumptions / delegated-choices-now-made awaiting user/qa confirmation*, not unanswered
> blockers — each is already reified into a requirement and/or a §4.1 pin with a default
> consistent with the locked ticket and the constitution. If qa-reviewer or the user overrides
> any default, the corresponding Rn / Dn changes and this section's entry is struck. No entry
> here halts development.

## 10. Observability plan

### 8a — Operational events (always required)

CONSTITUTION §8a requires "every business-meaningful state change" to emit one structured log
line, where business-meaningful means "anything an auditor, support engineer, or product manager
would want to reconstruct after the fact." `LruCache` is an **in-process library data structure**:
it performs no I/O, no persistence, and no network call; every method is synchronous and observable
entirely through its return value, the read-only stats properties (R10), or a propagated exception.
Its state changes (insert, overwrite, hit, miss, eviction, remove, clear) are local data-structure
mutations, not business events — the *caller* is the boundary that owns the `trace_id`/`actor_id`/
`resource_id` context and decides whether a given cache operation is business-meaningful enough to
log. Emitting a structured log line from inside the primitive would (a) attach no correlation
context the cache legitimately possesses, (b) duplicate or pre-empt the caller's own boundary
logging, and (c) inject an I/O side effect into a structure the ticket (§7, §8) specifies as
in-memory and side-effect-free.

The one state change that drops data — eviction — is the documented contract of a bounded cache,
not silent loss (CONSTITUTION §2.3): it is surfaced to the caller via the `evictions` counter
(R7, R10), which is the in-process equivalent of "log + surface the loss" appropriate to a library
primitive. A caller that needs an eviction *log line* reads the counter and logs it with its own
correlation context.

**Therefore this feature emits no structured operational log line, and that is the correct reading
of §8a, not an omission.** The mapping "every spec-mandated success criterion and failure mode has
a corresponding logged event" is satisfied via the directly-asserted return/raise/counter behavior
in the §8 acceptance tests rather than by log inspection. `observability-auditor` should verify
this justification rather than expect an event-table row.

| Spec ref | Event name (enum const) | Level | Key fields | Metric / Alert |
| --- | --- | --- | --- | --- |
| — | _none — in-process library primitive, no business state change; eviction surfaced via `evictions` counter (R7, R10), see justification above_ | — | — | — |

> §8b (audit), §8c (analytics), §8d (security events) are all `scope: disabled` in CONSTITUTION
> §8 and the ticket §11 — their tables are intentionally omitted per the template rule. No audit,
> analytics, or security-monitoring events are introduced by this feature.

## 10.1 Test execution requirements

Inherited from CONSTITUTION §4. No feature-specific exceptions.

- Local isolation: inherit §4.1 — none needed; `LruCache` is a pure in-memory structure requiring
  no external infrastructure. Tests run in-process with pytest, no services.
- E2E policy: inherit §4.3 — disabled; unit tests are sufficient. Tests live at
  `tests/unit/test_cache.py` (ticket §3, §12).
- Coverage target: inherit §4 coverage floor (0 %, tracked not gated). Coverage is a smoke alarm
  here, not a goal; the acceptance criteria in §8 are the real bar.
