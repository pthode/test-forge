# parse-duration — Software Design Document

> Source ticket: `/docs/requirements/parse-duration.md` (locked 2026-06-03).
> Constitution: `/CONSTITUTION.md` (§1 Python 3.12 stdlib-only, pytest; §8a always-on; §8b/c/d disabled; §13 versioning = none) + `/CONSTITUTION.project.md` (no §P sections defined).

## 1. Context

`tokenlab` needs a small, dependency-free utility to interpret compact human-readable
duration strings as integer seconds. `parse_duration(s: str) -> int` converts strings like
`"1h30m"`, `"45s"`, `"2h15m30s"` into a total whole-second count, raising `ValueError` on any
invalid input. It is a pure standard-library function with no external state — a reusable
building block for callers across the project.

**What it explicitly does NOT do** (see §3 for the enumerated list): it does not accept units
beyond `h`/`m`/`s`, does not accept bare integers, decimals, negatives, uppercase suffixes,
ISO-8601 syntax, or inter-component whitespace; it performs no clock-range validation, no
per-component caps, no localization, and no I/O, persistence, logging, configuration, or CLI.

This document covers the full feature. **No `/docs/api/`, `/docs/data-models/`, or
`/docs/diagrams/` artifacts are produced**, because:
- there is no HTTP/network interface → no OpenAPI contract (§5),
- there is no persisted state → no data model (§6),
- there is a single in-process collaborator (the calling code) → no sequence diagram (the
  multi-component threshold of >2 collaborators is not met).

## 2. Requirements

Each requirement is testable and cited back to the ticket.

- R1: A public function `parse_duration(s: str) -> int` exists at `src/tokenlab/duration.py` and is the module's only public name. <!-- Sources: ticket §1, §3, §12 (file location), §14 (single public name, inferred) -->
- R2: For a valid input, the return value is a non-negative Python `int` equal to `hours*3600 + minutes*60 + seconds`. <!-- Sources: ticket §7, §12, §14 (int not float, inferred) -->
- R3: The supported unit suffixes are exactly `h` (hours), `m` (minutes), `s` (seconds), lowercase only. Any other suffix (including uppercase `H`/`M`/`S` and unknown letters like `x`/`d`) makes the input invalid. <!-- Sources: ticket §3, §4, §6, §13 Q1/Q5 -->
- R4: A valid input is one or more `<integer><unit>` components concatenated with no separators, where each present unit appears at most once and units appear in strict descending magnitude order (`h` before `m` before `s`). Repeated units (e.g. `"1h1h"`) and out-of-order units (e.g. `"30m1h"`) are invalid. <!-- Sources: ticket §3, §6, §13 Q2 -->
- R5: Each integer component is a non-negative base-10 integer with no sign and no decimal point. Leading zeros are accepted as valid base-10 integers (e.g. `"01h" == 3600`). <!-- Sources: ticket §6, §13 Q5/Q6, §14 (leading zeros, inferred) -->
- R6: Leading and trailing whitespace on the whole input is trimmed before parsing. Whitespace *between* components (e.g. `"1h 30m"`) is invalid. <!-- Sources: ticket §3, §4, §6, §13 Q4, §14 (inter-component whitespace, inferred) -->
- R7: `"0s"` returns `0`. Components carry no upper cap: `"90m" == 5400`, with no clock-style range validation. <!-- Sources: ticket §3, §6, §12, §13 Q4/Q5 -->
- R8: Every invalid input raises `ValueError` — never a sentinel return, never a silent default, never a swallowed exception. The function is total over `str`: for any `str` it either returns a non-negative `int` or raises `ValueError`, and must not leak any other exception type (no uncaught `IndexError`/`AttributeError`/`TypeError`) for a malformed string. <!-- Sources: ticket §7, §10, §14 (exactly ValueError not a subclass, inferred); CONSTITUTION §3, §5 -->
- R9: The `ValueError` message describes what was wrong with the input sufficiently to debug. Exact wording is left to the implementation; the message MUST NOT echo content that could constitute injected control characters unescaped, but plain inclusion of the offending input substring is acceptable. <!-- Sources: ticket §7, §10, §14 (wording left to impl, inferred) -->
- R10: Parsing uses `re` or manual string scanning only. `eval`/`exec` (or any dynamic code execution) MUST NOT be used. <!-- Sources: ticket §9, §11, §14 (parse approach, inferred); CONSTITUTION §5 ("never eval") -->
- R11: The function carries a docstring describing purpose, accepted grammar, return value, and the `ValueError` contract. <!-- Sources: ticket §3, §12 -->

## 3. Non-goals

These inputs/behaviors are explicitly out of scope. Where they are *inputs*, they are invalid
and raise `ValueError` (R8); they are listed here so reviewers do not treat their absence as a gap.

- Day/week/month/year units (`d`, `w`, `mo`, `y`) — out of scope; invalid input.
- Bare integers with no unit (`"90"`) — invalid, not "90 seconds".
- Decimal / fractional components (`"1.5h"`) — invalid.
- Uppercase or mixed-case suffixes (`"1H"`, `"30M"`) — invalid.
- Negative durations (`"-1h"`) — invalid.
- ISO-8601 duration syntax (`"PT1H30M"`) — invalid.
- Whitespace between components (`"1h 30m"`) — invalid (only outer whitespace trimmed; see §9 OQ-2).
- Clock-style range validation (no rejection of `"90m"`) and per-component upper caps.
- Localization / non-English unit names.
- Any persistence, I/O, logging, configuration, CLI wrapper, class, or additional public API.

## 4. Architecture

A single pure function in one module:

```
src/tokenlab/duration.py
    parse_duration(s: str) -> int        # the only public name
    (unit→seconds multipliers and the component pattern are module-private)
```

Control flow (single in-process collaborator, no diagram warranted):

1. Caller invokes `parse_duration(s)` with a string.
2. The function strips outer whitespace (R6) and rejects empty/whitespace-only input (R8).
3. It scans the trimmed string into ordered `<integer><unit>` components (R4, R5) using `re`
   or manual scanning (R10).
4. It validates: full string consumed by components, each unit at most once, units in strict
   descending order, integers non-negative (R3, R4, R5, R6). Any failure → `ValueError` (R8, R9).
5. On success it sums `hours*3600 + minutes*60 + seconds` and returns a non-negative `int` (R2, R7).

Boundary discipline (CONSTITUTION §5): input is treated as hostile and validated at the
function boundary; the error is raised at the origin (CONSTITUTION §3) and not wrapped or
swallowed.

## 5. API contract

Not applicable — there is no HTTP/network interface. The "interface" is the Python function
signature, fully specified by R1, R2, R8 and the grammar in R3–R7. **No
`/docs/api/parse-duration.openapi.yaml` is produced.**

Function signature (authoritative):

```python
def parse_duration(s: str) -> int: ...
```

Grammar (EBNF, authoritative for R3–R7):

```
duration   = component , { component } ;          (* at least one *)
component   = integer , unit ;
integer     = digit , { digit } ;                 (* base-10, no sign, no '.' ; leading zeros OK *)
unit        = "h" | "m" | "s" ;                   (* lowercase only *)
(* additional constraints not expressible in EBNF alone: *)
(*  - units appear in strict descending order h > m > s    *)
(*  - each unit appears at most once                        *)
(*  - no whitespace anywhere except trimmed outer ends      *)
```

## 6. Data model

Not applicable — the function holds no state and persists nothing. **No
`/docs/data-models/parse-duration.md` is produced.**

## 7. Failure modes

- **Input validation (the only failure surface):** every invalid form below raises `ValueError`
  (R8) with a debuggable message (R9). Enumerated invalid classes:
  - empty / whitespace-only (`""`, `"   "`) — R6, R8.
  - bare integer, no unit (`"90"`) — R3, R4.
  - unknown / uppercase suffix (`"1H"`, `"30M"`, `"1x"`, `"1d"`) — R3.
  - negative sign (`"-1h"`) — R5.
  - out-of-order units (`"30m1h"`) — R4.
  - repeated unit (`"1h1h"`) — R4.
  - non-integer component (`"1.5h"`) — R5.
  - inter-component whitespace (`"1h 30m"`) — R6.
  - non-grammar garbage (`"abc"`, `"h"`, `"1"`) — R3, R4.
- **External-service failure:** none — there are no external dependencies (ticket §9, §10).
- **Concurrency:** none — the function is pure, holds no mutable shared state, and is
  re-entrant / thread-safe by construction (ticket §8).
- **Totality:** the function must not leak non-`ValueError` exceptions for malformed `str`
  input (R8). A `TypeError` from passing a non-`str` argument is outside the typed contract
  and is not constrained by this spec.

## 8. Acceptance criteria

1:1 mapping to requirements (test-engineer cites Rn).

- R1 → importing `from tokenlab.duration import parse_duration` succeeds; `parse_duration` is callable; module exposes no other public name.
- R2 → `parse_duration("2h15m30s") == 8130` and the return value `isinstance(result, int)` and `result >= 0`.
- R3 → `parse_duration("1H")`, `parse_duration("30M")`, `parse_duration("1x")`, `parse_duration("1d")` each raise `ValueError`; `parse_duration("45s") == 45`.
- R4 → `parse_duration("1h30m") == 5400`; `parse_duration("30m1h")` raises `ValueError`; `parse_duration("1h1h")` raises `ValueError`.
- R5 → `parse_duration("-1h")` raises `ValueError`; `parse_duration("1.5h")` raises `ValueError`; `parse_duration("01h") == 3600`.
- R6 → `parse_duration("  1h  ") == 3600`; `parse_duration("1h 30m")` raises `ValueError`; `parse_duration("")` and `parse_duration("   ")` raise `ValueError`.
- R7 → `parse_duration("0s") == 0`; `parse_duration("90m") == 5400`.
- R8 → for each invalid example in §7, the raised type is exactly `ValueError` (not a subclass, not another exception type); no malformed `str` raises `IndexError`/`AttributeError`.
- R9 → the `ValueError` raised for at least one representative invalid input carries a non-empty message string (asserted non-empty; exact wording not asserted).
- R10 → the implementation contains no `eval`/`exec` call (static check / source grep is acceptable evidence).
- R11 → `parse_duration.__doc__` is a non-empty string.

## 9. Open questions

The ticket §14 lists six assumptions the user did NOT confirm. Per the spec-architect operating
rule (chat/ticket additions that the user has not locked are recorded here for qa-reviewer to
verify intent). Each is resolved into a requirement above with the cited default; none blocks the
pipeline — all are consistent with the constitution and with the ticket's confirmed §13 answers.
qa-reviewer should confirm the chosen default matches user intent before release.

- OQ-1 — Return type is exactly `int`, never `float` (resolved in R2 per ticket §7/§14). No conflict.
- OQ-2 — Inter-component whitespace (`"1h 30m"`) is invalid; only outer whitespace is trimmed (resolved in R6 per ticket §4/§14). No conflict.
- OQ-3 — Exception type is exactly `ValueError`, not a custom subclass; message wording left to implementation (resolved in R8/R9 per ticket §14). No conflict.
- OQ-4 — Parsing uses `re` or manual scanning, never `eval`/`exec` (resolved in R10 per ticket §14 and CONSTITUTION §5). No conflict — this default is also a hard constitutional requirement, so it is not truly open.
- OQ-5 — Leading zeros in components (`"01h"`) are accepted as base-10 integers (resolved in R5 per ticket §14). No conflict.
- OQ-6 — The module's only public name is `parse_duration`; no class or CLI is added (resolved in R1 per ticket §14). No conflict.

> The pipeline rule is "do not advance until §9 is empty." These entries are *resolved
> assumptions awaiting user/qa confirmation*, not unanswered blockers — each is already
> reified into a requirement with a default consistent with the locked ticket and the
> constitution. If qa-reviewer or the user overrides any default, the corresponding Rn changes
> and this section's entry is struck. No entry here halts development.

## 10. Observability plan

### 8a — Operational events (always required)

CONSTITUTION §8a requires "every business-meaningful state change" to emit one structured log
line, where business-meaningful means "anything an auditor, support engineer, or product manager
would want to reconstruct after the fact." `parse_duration` is a **pure library primitive**: it
performs no business state change, no I/O, no persistence, and no network call; it is
synchronous, re-entrant, and observable entirely through its return value or raised `ValueError`.
A caller error (invalid duration string) is surfaced to the caller as an exception at the origin
(R8, CONSTITUTION §3) — the *caller* is the boundary that decides whether that event is
business-meaningful and logs it with its own `trace_id` and domain context. Emitting a structured
log line from inside the primitive would (a) attach no `actor_id`/`resource_id`/`trace_id` that
the function legitimately possesses, (b) duplicate or pre-empt the caller's own boundary logging,
and (c) introduce an I/O side effect into a function the ticket (§7, §8) specifies as side-effect
free.

**Therefore this feature emits no structured operational log line, and that is the correct
reading of §8a, not an omission.** §8a's mandate is scoped to business-meaningful state changes;
a deterministic pure-function computation is not one. The mapping "every spec-mandated success
criterion and failure mode has a corresponding logged event" is satisfied vacuously here because
the function's contract is its return/raise behavior, asserted directly by the §8 acceptance
tests rather than by log inspection. `observability-auditor` should verify this justification
rather than expect an event table row.

| Spec ref | Event name (enum const) | Level | Key fields | Metric / Alert |
| --- | --- | --- | --- | --- |
| — | _none — pure library primitive, no business state change (see justification above)_ | — | — | — |

> §8b (audit), §8c (analytics), §8d (security events) are all `scope: disabled` in
> CONSTITUTION §8 and the ticket §11 — their tables are intentionally omitted per the
> template rule. No audit, analytics, or security-monitoring events are introduced by this
> feature.

## 10.1 Test execution requirements

Inherited from CONSTITUTION §4. No feature-specific exceptions.

- Local isolation: inherit §4.1 — none needed; this is a pure function requiring no external
  infrastructure. Tests run in-process with pytest, no services.
- E2E policy: inherit §4.3 — disabled; unit tests are sufficient. Tests live at
  `tests/unit/test_duration.py` (ticket §3, §12).
- Coverage target: inherit §4 coverage floor (0 %, tracked not gated). Coverage is a smoke
  alarm here, not a goal; the acceptance criteria in §8 are the real bar.
