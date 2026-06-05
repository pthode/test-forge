# tokenlab — Backlog

Tech debt, deferred fixes, and known cleanup items. Reviewers append entries during the pipeline; the team works through them with `refactor-specialist` or `/autopilot` as capacity allows. See CONSTITUTION.md §12 for the discipline that governs this file.

## How this file works

- **Reviewers write here, not into feature PRs.** Every minor finding from `qa-reviewer`, `code-reviewer`, `security-auditor`, `performance-analyst`, `ux-consultant`, or `observability-auditor` lands here as a numbered entry. Inline minor fixes during a feature PR are forbidden — they bloat scope and drown the diff.
- **IDs are sequential, never reused.** Use `B-001`, `B-002`, … in order. When you close an entry, move it to "Closed entries" below; do not renumber.
- **Take an item:** invoke `refactor-specialist B-NNN` for behavior-preserving cleanup, or `/autopilot <description referencing B-NNN>` for items that need full pipeline treatment (schema changes, new contracts, etc.).
- **Deadlines are real.** When a pipeline run starts and finds an entry past its deadline, the orchestrator promotes that entry to a `major` finding on the current iteration. Don't write deadlines you don't intend to honor.

## Active entries

## B-001 — parse_duration param `s` abbreviates against §3

- **Created:** 2026-06-03
- **Source:** code-reviewer finding during feature `parse-duration` iteration 1
- **Type:** tech-debt
- **Severity:** minor (singleton)
- **Suggested fix:** `src/tokenlab/duration.py:18` — param `s: str` violates §3 "full words over abbreviations". Spec-locked (R1/§5), so resolution requires a spec-architect signature change to e.g. `text: str` before the rename.
- **Deadline:** 2026-09-01

## B-002 — Duplicated ValueError message construction

- **Created:** 2026-06-03
- **Source:** code-reviewer finding during feature `parse-duration` iteration 1
- **Type:** refactor
- **Severity:** minor (singleton)
- **Suggested fix:** `src/tokenlab/duration.py:50,58` — identical `raise ValueError(f"invalid duration string: {trimmed!r}")` twice. Extract a single local raise helper / message const if a third branch appears.
- **Deadline:** 2026-09-01

## B-003 — Parallel unit dicts must be kept in sync

- **Created:** 2026-06-03
- **Source:** code-reviewer finding during feature `parse-duration` iteration 1
- **Type:** refactor
- **Severity:** minor (singleton)
- **Suggested fix:** `src/tokenlab/duration.py:12,15` — `_UNIT_SECONDS` and `_UNIT_ORDER` are parallel dicts over the same key set. Consider one insertion-ordered structure deriving rank from position to remove sync risk.
- **Deadline:** 2026-09-01

## B-004 — parse_duration: add explicit input-length guard

- **Created:** 2026-06-03
- **Source:** security-auditor finding during feature `parse-duration` iteration 1
- **Type:** tech-debt
- **Severity:** minor (singleton)
- **Suggested fix:** `src/tokenlab/duration.py:60` — reject trimmed inputs over a generous length cap (~64 chars) at the boundary so the unbounded-bignum local-DoS bound is intrinsic to the function rather than dependent on the process-global CPython `int_max_str_digits` setting. Caps total input length, not the per-value range R7 intentionally leaves uncapped. ReDoS itself was probed and is linear/clear.
- **Deadline:** 2026-09-01

## B-005 — Document reliance on CPython int-string-digit guard for large-component cost ceiling

- **Created:** 2026-06-03
- **Source:** performance-analyst finding during feature `parse-duration` iteration 1
- **Type:** tech-debt
- **Severity:** minor (singleton)
- **Suggested fix:** `src/tokenlab/duration.py:60` — the O(n²) cost of `int(value)` on a very large component is bounded only by CPython's global `int_max_str_digits` guard (default 4300), which raises a spec-compatible `ValueError` (R8). If a caller raises that global limit the cost ceiling disappears. Add a brief docstring/comment noting the dependency, or an explicit component-length check. No behavior change required now; measured worst case under the default guard is sub-millisecond. (Related to B-004 — candidate for grooming consolidation.)
- **Deadline:** 2026-09-01

## B-006 — Bump GitHub Actions versions before Node 20 EOL (2026-06-16)

- **Created:** 2026-06-03
- **Source:** release-engineer finding during feature `parse-duration` iteration 1 (CI deprecation annotation)
- **Type:** tech-debt
- **Severity:** minor (singleton)
- **Suggested fix:** `.github/workflows/ci.yml` — `actions/checkout@v4` and `actions/setup-python@v5` run on Node 20, which GitHub forces to Node 24 on 2026-06-16. Bump to the Node-24-compatible major versions (owned by devops-engineer) before that date. Non-blocking today.
- **Deadline:** 2026-06-16

## B-007 — LruCache: no explicit int type guard on capacity

- **Created:** 2026-06-05
- **Source:** qa-reviewer finding during feature `lru-cache` iteration 1
- **Type:** tech-debt
- **Severity:** minor (singleton)
- **Suggested fix:** `src/tokenlab/cache.py:36` — `if capacity < 1` accepts `float` (`LruCache(1.5)` → capacity `1.5`) and `bool` (`LruCache(True)` → capacity `1`). Within spec (§7/OQ-2 only requires non-comparable types not be silently accepted; an `isinstance` check is not mandated), but a `float`/`bool` capacity is a latent surprise. Add an optional `isinstance(capacity, int) and not isinstance(capacity, bool)` guard, or a test pinning the current float-accepting behavior.
- **Deadline:** 2026-09-01

## B-008 — LruCache class name diverges from §3 acronym-casing

- **Created:** 2026-06-05
- **Source:** code-reviewer finding during feature `lru-cache` iteration 1
- **Type:** docs/convention
- **Severity:** minor (singleton)
- **Suggested fix:** `src/tokenlab/cache.py:9` — CONSTITUTION §3 keeps ≤3-letter acronyms uppercase (`LRUCache`), but the name `LruCache` is fixed by the spec (R1/§4/§5), so the developer correctly followed it. Reconciliation is spec-architect's: either amend the spec to `LRUCache`, or document a deliberate §3 exception for the spec-mandated name. Not a developer defect.
- **Deadline:** 2026-09-01

## B-009 — LruCache: get() hit path does two hash lookups

- **Created:** 2026-06-05
- **Source:** code-reviewer finding during feature `lru-cache` iteration 1
- **Type:** refactor
- **Severity:** minor (singleton)
- **Suggested fix:** `src/tokenlab/cache.py:52-55` — the hit path does `__contains__` then `__getitem__` (two probes). Optional single-lookup sentinel refactor (`value = self._store.get(key, _MISSING)`). Readability tradeoff; amortized O(1) either way, so R16 is unaffected. Low priority.
- **Deadline:** 2026-09-01

## B-010 — LruCache: docstring should note capacity bounds entry count, not bytes

- **Created:** 2026-06-05
- **Source:** security-auditor finding (F1, LOW) during feature `lru-cache` iteration 1
- **Type:** docs
- **Severity:** minor (singleton)
- **Suggested fix:** `src/tokenlab/cache.py:10-28` — class docstring does not state that `capacity` bounds entry *count*, not memory bytes. Add one sentence noting that callers storing untrusted/unbounded values should bound value size themselves. Doc-hardening only; no exploit, no code change.
- **Deadline:** 2026-09-01

<!-- Reviewers append entries here. Format per CONSTITUTION.md §12.2. -->

## Closed entries (audit trail — one release cycle)

<!-- Move resolved entries here. Archive entries older than one release cycle. -->
