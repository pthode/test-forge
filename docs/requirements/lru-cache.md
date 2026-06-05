# lru-cache — Requirements Ticket

> Locked on 2026-06-05 by requirements-intake. Reopening requires a new autopilot run.

## 1. One-line summary
A bounded in-memory LRU cache class `LruCache` for tokenlab, with `get`/`put`, full mutation API (membership check, `remove`, `clear`), and readable hit/miss/eviction/size statistics — standard library only.

## 2. Context
tokenlab needs a small, dependency-free caching primitive for reuse across the library. This ticket adds a single self-contained class at `src/tokenlab/cache.py` that stores key→value pairs up to a fixed capacity and evicts the least-recently-used entry when inserting a new key would exceed capacity. It augments the existing stdlib-only utility set (alongside the duration parser); it does not replace any existing component.

## 3. In scope
- A class `LruCache` living at `/src/tokenlab/cache.py`.
- Construction with a fixed positive integer `capacity`.
- `get(key, default=None)` — returns the stored value on a hit, or the supplied `default` (None by default) on a miss. A hit refreshes recency (moves the entry to most-recently-used). A miss counts as a miss.
- `put(key, value)` — inserts a new key→value pair, or overwrites the value for an existing key. In both cases the entry becomes most-recently-used. Overwriting an existing key does NOT grow size. Inserting a new key at full capacity evicts the least-recently-used entry first.
- True-LRU recency semantics: both `get` (on a hit) and `put` mark an entry most-recently-used; eviction always removes the genuinely least-recently-used entry.
- Storing `None` as a value: `put(k, None)` stores `None`, and a later `get(k)` is a hit returning `None` — distinct from an absent key.
- Statistics exposing all five fields: `hits`, `misses`, `evictions`, current `size`, and `capacity`.
- A `reset_stats()` (or equivalent) that zeroes the counters (`hits`, `misses`, `evictions`) WITHOUT clearing cached entries (size and capacity are unaffected).
- Non-recency-affecting membership check (`__contains__` / `peek`) — checking presence does NOT move the entry in recency order and does NOT count as a hit or miss.
- `remove(key)` — removes a single entry if present.
- `clear()` — empties all cached entries.
- Unit tests at `/tests/unit/test_cache.py` derived from the success criteria below.

## 4. Out of scope (explicit non-goals)
- No persistence to disk, database, or any external store — the cache is purely in-memory and lives for the lifetime of the instance.
- No external runtime dependencies — standard library only (CONSTITUTION §1).
- No TTL / time-based expiry — eviction is recency-and-capacity driven only.
- No size/weight-based eviction (entries are counted by key, not by byte weight).
- No async API — synchronous methods only.
- No serialization / pickling support beyond whatever Python provides by default.
- No CLI, no HTTP surface, no UI of any kind.

## 5. Actors and triggers
- Initiated programmatically by any in-process Python caller that imports `LruCache` from `tokenlab.cache` and invokes its methods. No external actors; no network or user-facing trigger.

## 6. Inputs
- **Constructor:** `capacity: int`. Must be `>= 1`; a value of `0` or negative raises `ValueError`. (A1/A4)
- **`get(key, default=None)`:** `key` is any hashable object; `default` is any object (defaults to `None`).
- **`put(key, value)`:** `key` is any hashable object; `value` is any object (including `None`).
- **`remove(key)`, membership check, `peek`:** `key` is any hashable object.
- Keys must be hashable. Passing an unhashable key surfaces the natural `TypeError` from the underlying mapping (inferred — flag if wrong); no custom validation is layered on top.

## 7. Outputs
- **`get`** returns the stored value (on a hit) or the supplied `default` (on a miss). No exception on miss.
- **Statistics** are read via the five exposed fields (`hits`, `misses`, `evictions`, `size`, `capacity`). Exact accessor shape (properties, a stats object/namedtuple, or a method returning a mapping) is an implementer decision recorded under "Decisions taken".
- **Membership check** returns a boolean.
- `put`, `remove`, `clear`, `reset_stats` mutate state; their return shapes are implementer decisions (record under "Decisions taken").

## 8. Persistence
- None. Purely in-memory for the lifetime of the `LruCache` instance.

## 9. External dependencies
- None. Standard library only (CONSTITUTION §1).

## 10. Failure behavior
- **Invalid capacity** (`0` or negative) at construction → raises `ValueError`. Fatal to construction; recoverable by the caller passing a valid capacity.
- **Unhashable key** → the natural `TypeError` from the underlying mapping propagates (inferred — flag if wrong). Not caught or wrapped.
- **`remove(key)` on an absent key** → behavior (no-op vs. raise) is an implementer decision recorded under "Decisions taken"; spec-architect should pin it explicitly in the SDD.
- No external dependency exists, so there is no I/O, network, or service-failure path to handle.

## 11. Non-functional constraints
- **Stack:** Python 3.12, standard library only, no external runtime dependencies (CONSTITUTION §1).
- **Performance:** No performance SLA — CONSTITUTION §6 budgets are TBD and this is not a latency-sensitive feature. `performance-analyst` limits itself to structural checks (e.g., that `get`/`put` are not accidentally O(n)); a typical LRU implementation achieves amortized O(1) for `get`/`put`, but no specific budget is mandated.
- **Observability:** No structured events required for this feature. CONSTITUTION §8a (operational observability) applies to business-meaningful state changes in production deployments; an in-process library data structure emits none. §8b (audit), §8c (analytics), and §8d (security monitoring) are all `scope: disabled`. This feature introduces no new audit events, analytics events, or security-monitoring trigger conditions.
- **Accessibility:** N/A — no UI surface (CONSTITUTION §7.2 lists no UI surfaces for this project).
- **Security:** No auth, secrets, crypto, network, file, or shell surface. Input is in-process Python objects from a trusting caller.
- **Test:** pytest; tests derived from the spec/success criteria, not the implementation (CONSTITUTION §4, §4.2).

## 12. Success criteria
- Constructing with `capacity >= 1` succeeds; constructing with `0` or a negative capacity raises `ValueError`.
- `get` on an absent key returns the supplied `default` (None when omitted) and increments the miss counter.
- `get` on a present key returns the stored value, increments the hit counter, and refreshes the entry to most-recently-used.
- `put` on a new key inserts it as most-recently-used and increases `size` by one (until capacity is reached).
- `put` on an existing key overwrites the value, marks it most-recently-used, and leaves `size` unchanged.
- Inserting a new key when at capacity evicts the genuinely least-recently-used entry, increments the eviction counter, and keeps `size == capacity`.
- Recency is true-LRU: a `get` hit on an entry protects it from being the next eviction victim; the entry not touched longest is the one evicted.
- `put(k, None)` followed by `get(k)` returns `None` and counts as a hit; this is distinguishable from `get` on an absent key (which returns the default and counts as a miss).
- All five stats fields (`hits`, `misses`, `evictions`, `size`, `capacity`) are readable and accurate after a sequence of operations.
- `reset_stats()` zeroes `hits`, `misses`, and `evictions` while leaving cached entries intact (`size` and `capacity` unchanged); subsequent operations resume counting from zero.
- The membership check (`__contains__` / `peek`) reports presence correctly, does NOT change recency order, and does NOT alter the hit/miss counters.
- `remove(key)` deletes a present entry (reducing `size` by one); subsequent `get` on that key is a miss.
- `clear()` empties all entries (`size == 0`); `capacity` is unchanged; stats-clearing behavior on `clear()` is an implementer decision pinned by spec-architect.

## 13. Answered questions (intake transcript)
| # | Question | Answer |
|---|----------|--------|
| Q1 | `get(key)` on a miss — behavior? | dict.get style: `get(key, default=None)` returns the supplied default (None by default); access counts as a miss. |
| Q2 | `put` on an existing key? | Overwrite the value AND mark it most-recently-used; size does not grow. |
| Q3 | `get` on a present key — recency? | A hit refreshes recency (moves entry to most-recently-used). True LRU. |
| Q4 | Capacity validation? | Capacity must be `>= 1`; `0` or negative raises `ValueError`. |
| Q5 | `None` as a value? | Yes — `None` is storable and distinct from absent; `put(k, None)` stores None and a later `get(k)` is a hit returning None. |
| Q6 | Stats exposure? | Expose all five fields (hits, misses, evictions, current size, capacity) and a `reset_stats()` (or equivalent) that zeroes counters without clearing cached entries. |
| Q7 | Mutation API scope? | `get` + `put` + non-recency-affecting membership check (`__contains__`/`peek`) + `remove(key)` + `clear()`. |

## 14. Inferred assumptions (NOT confirmed by user)
- Standard library only; no external runtime dependencies (inferred — aligned with CONSTITUTION §1; flag if wrong).
- No persistence — purely in-memory for the instance lifetime (inferred — flag if wrong).
- Keys must be hashable; an unhashable key surfaces the natural `TypeError` from the underlying mapping rather than a custom-validated error (inferred — flag if wrong).
- No observability events for this feature — §8a covers production state changes, not an in-process data structure; §8b/§8c/§8d are all `scope: disabled` (inferred — flag if wrong).
- No performance SLA — CONSTITUTION §6 budgets are TBD and the feature is not latency-sensitive (inferred — flag if wrong).
- spec-architect MAY override these if they discover a conflict, but MUST cite the conflict in §9 of the resulting SDD.

### Decisions taken (deferred to implementer / spec-architect)
The following were explicitly left as implementer decisions during intake and must be pinned by spec-architect in the SDD (and recorded here when finalized):
- **Thread-safety model:** whether `LruCache` is documented as not thread-safe, or guarded by a lock. Default expectation: not thread-safe unless the SDD states otherwise.
- **Internal data structure:** e.g. `collections.OrderedDict` vs. a hand-rolled doubly-linked-list + dict. Any choice that meets the recency and amortized-O(1) expectations is acceptable.
- **Exact exception classes beyond `ValueError`:** any error types raised for cases not enumerated above.
- **`remove(key)` on an absent key:** no-op vs. raise (e.g. `KeyError`).
- **Statistics accessor shape:** individual properties vs. a stats object/namedtuple vs. a method returning a mapping.
- **`reset_stats` vs. equivalent naming**, and **whether `clear()` also resets stats** (A6 only mandates that `reset_stats` does NOT clear entries; the converse is unspecified).
