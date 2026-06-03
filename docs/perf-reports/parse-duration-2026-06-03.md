# Performance report — parse-duration (tokenlab) — 2026-06-03

**Mode:** autopilot, Phase 3, iteration 1
**Verdict: ACCEPT** (no REJECT). 1 minor → `BACKLOG.md` (B-005).

(Persisted by the orchestrator from performance-analyst's returned findings — the agent is read-only.)

Budget: CONSTITUTION §6 is TBD/unset (non-latency-sensitive stdlib library). Review limited to structural issues per §6 fallback.

## Summary

| Severity | Count |
| --- | --- |
| blocker | 0 |
| major | 0 |
| minor | 1 |

## Pattern checks

- **N+1 / missing indexes / blocking-async:** N/A — pure in-process function, no DB/network/IO, no async.
- **Unbounded loops/recursion:** the `for` over `findall(trimmed)` is bounded to ≤3 components on valid input (rank-monotonicity rejects repeats); `findall` is single-pass O(len). No recursion. Not a finding.

## Regex backtracking (primary concern)

Pattern `\A(?:[0-9]+[hms])+\Z` has the `(?:X+Y)+` shape but is **de-fanged** by the single-char delimiter `[hms]` between digit runs — every input position has exactly one parse. Benchmarked linear (O(n)) up to 2M chars:

| Input | Length | Match | Time |
|---|---|---|---|
| `("1h"*20000)+"x"` | 40,001 | False | 6.3 ms |
| `("1"*50000)+"!"` | 50,001 | False | 1.0 ms |
| `"9"*100000` | 100,000 | False | 1.0 ms |
| `"1h"*1000000` | 2,000,000 | True | 240 ms |

Doubling input doubles time — no superlinear blowup.

## Large-integer conversion

`int(value)` is the only other potentially superlinear op; bounded by CPython's 4300-digit `int_max_str_digits` guard which raises a spec-compatible `ValueError` (R8). Sub-millisecond. Spec-compatible, not a defect.

## Minor finding (B-005)

The large-component cost ceiling depends on the process-global `int_max_str_digits` setting rather than `parse_duration`'s own validation. Correct today; document the dependency or add an explicit length check. No behavior change required.
