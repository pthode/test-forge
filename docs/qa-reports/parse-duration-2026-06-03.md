# QA Review — `parse_duration` (tokenlab) — 2026-06-03

**Mode:** autopilot, Phase 3, iteration 1
**Verdict: APPROVED**

(Persisted by the orchestrator from qa-reviewer's returned findings — the agent is read-only.)

## Test suite

- `python -m pytest -q` → **82 passed in 0.09s**, exit code **0**. No skips, xfails, or warnings.

## Coverage matrix (requirement → impl → test → doc)

| Req | Impl (`src/tokenlab/duration.py`) | Test (`tests/unit/test_duration.py`) | Doc (`README.md`) |
|---|---|---|---|
| R1 public single name | def + only other module-level non-`_` name is `re` | `test_r1_*` (3) | Usage signature |
| R2 non-neg int sum | integer fold | `test_r2_*` (3) | "non-negative int = h*3600+m*60+s" |
| R3 lowercase h/m/s only | `[hms]` | `test_r3_*` (incl `1S 1x 1d 1w 1y`) | "exactly h/m/s lowercase" |
| R4 order + at-most-once | rank guard | `test_r4_*` + extra order/repeat | descending + at-most-once |
| R5 base-10, no sign/dot, leading zeros | `[0-9]+`, `int()` | `test_r5_*` (`+1h 1,5h 1e3s`) | "base-10, leading zeros" |
| R6 trim outer, reject inner ws | `s.strip()`, anchored pattern | `test_r6_*` (`\t \n 1 h 1h 30m`) | trim + internal-ws invalid |
| R7 zero, no caps | no cap logic | `test_r7_*` (`100h 0h0m0s`) | "0s→0, 90m→5400, no cap" |
| R8 exactly ValueError, total | single raise paths | `test_r8_*` (19 inputs ×2) | totality paragraph |
| R9 non-empty message | `invalid duration string: {trimmed!r}` | `test_r9_*` | troubleshooting echoes input |
| R10 no eval/exec | uses `re` only (Grep clean) | `test_r10_*` | spec §5 |
| R11 docstring | docstring present | `test_r11_*` | documents usage |

## Ticket → spec coverage

Every §3 in-scope item maps to R1–R11; every §12 success criterion has a matching test. Every §4 out-of-scope item is structurally excluded by the anchored pattern `\A(?:[0-9]+[hms])+\Z`. No gap, no leakage.

## §14 inferred-assumption drift check

All six inferred assumptions (int-not-float, inter-component whitespace invalid, exactly `ValueError`, no eval/exec, leading zeros accepted, sole public name) match the implementation with **zero drift**.

## Constitution check

§1 stdlib-only, §3 style, §4 spec-derived tests, §5 input-hostile + no eval, §8a vacuous-coverage justification correct, §13 versioning=none → no CHANGELOG, §14 autonomous — all satisfied. `CONSTITUTION.project.md` defines no §P sections; no contradiction.

## Definition of Done (§9, applicable subset)

Spec exists & matches ✓ · tests green ✓ · README reflects change ✓ · migrations N/A · no blocker/major open from this review ✓.

## REJECT blocks

None.

## Minor findings

None from qa-reviewer directly. (code-reviewer, security-auditor, performance-analyst minors are recorded as B-001…B-005 in `BACKLOG.md`.)
