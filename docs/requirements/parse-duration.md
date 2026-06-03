# parse-duration — Requirements Ticket

> Locked on 2026-06-03 by requirements-intake. Reopening requires a new autopilot run.

## 1. One-line summary
A pure standard-library Python function `parse_duration(s: str) -> int` that converts a human-readable duration string (e.g. `"1h30m"`, `"45s"`, `"2h15m30s"`) into a total number of seconds, raising `ValueError` on invalid input.

## 2. Context
The `tokenlab` project (Python 3.12, stdlib-only per CONSTITUTION §1) needs a small, dependency-free utility to interpret compact human duration strings as integer seconds. This is a self-contained pure function with no external state — the kind of building block that callers across the project can reuse. It augments the library surface; it replaces nothing.

## 3. In scope
- A single public function `parse_duration(s: str) -> int` returning the total duration in whole seconds as a non-negative `int`.
- Supported unit suffixes: `h` (hours), `m` (minutes), `s` (seconds) — lowercase only.
- Multi-component strings where each present unit appears in strict descending order and at most once (e.g. `"2h15m30s"`, `"1h30m"`, `"45s"`).
- `"0s"` returns `0`.
- Leading and trailing whitespace on the input is trimmed before parsing.
- `ValueError` raised for every invalid input (see §6 / §10 for the full enumeration).
- Unit tests at `tests/unit/test_duration.py` covering valid parses and each rejection case.
- Docs: docstring on the function plus a usage entry in the project README.

## 4. Out of scope (explicit non-goals)
- Day/week/month/year units (`d`, `w`, etc.) — only `h`, `m`, `s`.
- Bare integers with no unit (`"90"`) — these are invalid, not "90 seconds".
- Decimal/fractional components (`"1.5h"`).
- Uppercase or mixed-case suffixes (`"1H"`, `"30M"`).
- Negative durations (`"-1h"`).
- ISO-8601 duration syntax (`"PT1H30M"`).
- Whitespace *between* components (`"1h 30m"`) — out of scope; treated as invalid (inferred — flag if wrong).
- Clock-style range validation (no rejection of `"90m"`; `90m` == `5400` seconds).
- Per-component upper caps.
- Localization / non-English unit names.
- Any persistence, I/O, logging, configuration, or CLI wrapper.

## 5. Actors and triggers
- Any Python caller within the `tokenlab` codebase that imports `parse_duration` and invokes it with a string argument. There is no human-facing UI, network, or scheduled trigger — invocation is purely programmatic.

## 6. Inputs
- A single positional argument `s: str` — a duration string.
- **Validation rules (input is valid only when all hold):**
  - Non-empty after trimming leading/trailing whitespace; `""` and whitespace-only inputs are invalid.
  - Composed of one or more `<integer><unit>` components with no separators between them.
  - Each integer component is a non-negative base-10 integer (no sign, no decimal point).
  - Each unit is one of `h`, `m`, `s`, lowercase only.
  - Units, where present, appear in strict descending magnitude order: `h` before `m` before `s`.
  - Each unit appears at most once. Repeats (`"1h1h"`) are invalid; out-of-order (`"30m1h"`) is invalid.
- **Examples that are valid:** `"45s"`, `"1h30m"`, `"2h15m30s"`, `"0s"`, `"90m"`, `"  1h  "` (outer whitespace trimmed).
- **Examples that are invalid (raise `ValueError`):** `""`, `"   "`, `"90"`, `"1H"`, `"30M"`, `"-1h"`, `"30m1h"`, `"1h1h"`, `"1.5h"`, `"1h 30m"`, `"abc"`, `"1x"`.

## 7. Outputs
- Return value: a non-negative `int` — the total number of seconds (`hours*3600 + minutes*60 + seconds`).
- No printing, no logging, no side effects.
- On invalid input: raises `ValueError`. The exception message should describe what was wrong with the input enough to debug (exact wording left to spec/implementation).

## 8. Persistence
- None. Pure function, no stored state.

## 9. External dependencies
- None. Standard library only, consistent with CONSTITUTION §1 (stdlib-only, no external runtime dependencies). A regular-expression / string-parse approach using `re` or manual scanning is acceptable; no third-party packages.

## 10. Failure behavior
- There are no external dependencies to fail.
- Every form of invalid input (enumerated in §6) is a **recoverable caller error** surfaced as `ValueError` — never a silent default, never a returned sentinel, never a swallowed exception. This aligns with CONSTITUTION §5 ("input is hostile by default; validate at the boundary") and §3 ("raise errors at the boundary they originate from; do not catch-and-swallow").
- The function must be total: for any `str` input it either returns a non-negative `int` or raises `ValueError`. It must not raise other exception types for malformed strings (e.g. no uncaught `IndexError`/`AttributeError` leaking through).

## 11. Non-functional constraints
- **Stack (CONSTITUTION §1):** Python 3.12, standard library only, no external runtime dependencies. Test framework: pytest.
- **Code style (CONSTITUTION §3):** full-word naming, one purpose per function, comments explain *why*, errors raised at origin.
- **Security (CONSTITUTION §5):** input treated as hostile; no `eval`/`exec` for parsing.
- **Performance (CONSTITUTION §6):** no budgets set (project is not latency-sensitive). The function operates on short strings; `performance-analyst` limited to structural checks only.
- **Accessibility (CONSTITUTION §7):** N/A — no UI surface (importable library module per §7.2).
- **Observability (CONSTITUTION §8):** §8a applies to production deployments; this is a pure stdlib function with no business state change to log. §8b/§8c/§8d are `disabled`. No new audit, analytics, or security-monitoring events introduced.

## 12. Success criteria
Testable conditions (`test-engineer` writes tests against these):
- `parse_duration("45s") == 45`
- `parse_duration("1h30m") == 5400`
- `parse_duration("2h15m30s") == 8130`
- `parse_duration("0s") == 0`
- `parse_duration("90m") == 5400` (no per-component cap)
- `parse_duration("  1h  ") == 3600` (outer whitespace trimmed)
- `parse_duration("")` raises `ValueError`
- `parse_duration("   ")` raises `ValueError`
- `parse_duration("90")` raises `ValueError` (bare integer, no unit)
- `parse_duration("1H")` raises `ValueError` (uppercase suffix)
- `parse_duration("-1h")` raises `ValueError` (negative)
- `parse_duration("30m1h")` raises `ValueError` (out of order)
- `parse_duration("1h1h")` raises `ValueError` (repeated unit)
- `parse_duration("1.5h")` raises `ValueError` (non-integer component)
- `parse_duration("abc")` raises `ValueError` (no valid components)
- The function lives at `src/tokenlab/duration.py`; tests at `tests/unit/test_duration.py`.
- The function carries a docstring; the README documents usage.

## 13. Answered questions (intake transcript)
| # | Question | Answer |
|---|----------|--------|
| Q1 | Which unit suffixes are supported? | `h`, `m`, `s` only. |
| Q2 | Component order and repeats? | Strict — units descending, each at most once; `"30m1h"` and `"1h1h"` raise `ValueError`. |
| Q3 | Are bare integers allowed? | No — every number needs a unit; `"90"` raises `ValueError`. |
| Q4 | Zero / empty / whitespace handling? | `""` and whitespace-only raise `ValueError`; `"0s"` returns `0`; leading/trailing whitespace trimmed. |
| Q5 | Case sensitivity and value range? | Lowercase suffixes only; non-negative integer components; no per-component cap (`90m` == 5400); no clock-range validation. |
| Q6 | Are negatives allowed? | No — `"-1h"` raises `ValueError`. |
| Q7 | File locations? | `src/tokenlab/duration.py` + `tests/unit/test_duration.py`. |

## 14. Inferred assumptions (NOT confirmed by user)
- Whitespace *between* components (`"1h 30m"`) is invalid and raises `ValueError` (only outer whitespace is trimmed) `(inferred — flag if wrong)`.
- Parsing uses `re` or manual string scanning, never `eval`/`exec` `(inferred — flag if wrong)`.
- The exception type is exactly `ValueError` (not a custom subclass); message wording is left to the implementation `(inferred — flag if wrong)`.
- The function returns a Python `int` (not `float`), since all components are whole and units convert to whole seconds `(inferred — flag if wrong)`.
- Component integers may have leading zeros (`"01h"` == 3600) — treated as valid base-10 integers `(inferred — flag if wrong)`.
- The module exposes `parse_duration` as its public name; no additional public API (no class, no CLI) is added `(inferred — flag if wrong)`.
- spec-architect MAY override these if they discover a conflict, but MUST cite the conflict in §9 of the resulting SDD.
