# Observability Report — parse_duration

> Feature: `parse_duration` · Project: `tokenlab` · Date: 2026-06-03
> Auditor: observability-auditor · Autopilot Phase 3, iteration 1
> Sources: `/docs/specs/parse-duration.md` (§2, §7, §8, §10), `/src/tokenlab/duration.py`,
> `/CONSTITUTION.md` §8 (§8a always-on; §8b/c/d disabled), `/CONSTITUTION.project.md` (no §P sections).

## Summary
| Severity | Count |
|----------|-------|
| blocker  | 0     |
| major    | 0     |
| minor    | 0     |

## Scope (Step 0 — enabled monitoring concerns)
| §8 concern | Scope marker | Action |
|------------|--------------|--------|
| §8a Operational observability | `always-on` | Full five-lens audit performed (baseline). |
| §8b Audit logging | `disabled` | Skipped — absence is NOT a finding. |
| §8c Product analytics | `disabled` | Skipped — absence is NOT a finding. |
| §8d Security event monitoring | `disabled` | Skipped — absence is NOT a finding. |

Spec §10 is present. It carries the §8a table (intentionally empty, with written justification)
and explicitly documents the omission of the §8b/c/d tables as correct under their `disabled`
scope. No "missing §10 table" finding applies.

## Event coverage matrix
| Spec ref | Event name | File:line | Level | Trace ID? | PII? |
|----------|-----------|-----------|-------|-----------|------|
| R1–R7 (success: return value) | — none (pure computation, observed via return value) | — | — | n/a | no |
| R8/R9 + §7 (failure: invalid input) | — none (surfaced to caller as `ValueError` at origin, src/tokenlab/duration.py:50,58) | — | n/a | no |

No event rows are expected. See justification verification below.

## Metrics & alerts
| Spec ref | Metric / Alert | Runbook? |
|----------|----------------|----------|
| (none) | none — no failure mode requires an operator-visible signal from a pure primitive | n/a |

No alert rules exist, therefore no missing-runbook blockers are possible.

## Verification of the spec's vacuous-satisfaction claim (§10)

The spec argues that a pure library primitive performing no business-meaningful state change
warrants no structured log line, satisfying §8a vacuously. I verified the four load-bearing
conditions:

1. **No business state change — CONFIRMED.** `parse_duration` is a single pure function:
   `s.strip()`, a regex match, an integer fold, a `return`. No module/global mutation, no argument
   mutation, no I/O. A package-wide grep for `logging|logger|print|log.|open(|requests|socket`
   returned zero matches. §8a's mandate is scoped to "business-meaningful state change"; a
   deterministic pure computation is not one.

2. **No operator-observable failure mode — CONFIRMED.** The only failure surface (§7) is input
   validation, raising `ValueError` at the origin (src/tokenlab/duration.py:50 and :58) per
   CONSTITUTION §3 and R8. The caller — which owns `trace_id`/`actor_id`/`resource_id` — is the
   boundary that decides whether the failure is business-meaningful and logs it. A log line from
   inside the primitive would carry none of the §8a-required correlation fields and would itself
   be a schema violation. No silent data loss occurs (CONSTITUTION §2.3): every invalid input is
   rejected with a raised exception, never coerced or defaulted, so the "log + surface the loss"
   trigger does not fire.

3. **No PII/secret leakage risk — CONFIRMED.** No log sink exists. The `ValueError` message uses
   `{trimmed!r}` (repr), which escapes control characters rather than echoing them raw (satisfies
   R9). The input domain is duration strings, not credential/PII material.

4. **§10 reasoning sound against §8a — CONFIRMED.** The empty-table-with-justification pattern
   correctly represents "vacuously satisfied for a pure primitive" and explicitly invites this
   verification rather than asserting a row. This matches §8a's intent.

Remaining lenses (schema discipline, log-level calibration, trace-ID propagation, metrics/alerts)
are not applicable: there are no log lines, no request path crossing services (this is an
in-process function call), and no failure mode requiring a counter or alert.

## Findings
None. No blocker, major, or minor findings. Nothing routed to `BACKLOG.md`.

## Verdict
APPROVED
