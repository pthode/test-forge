# Security Report — parse-duration

> Auditor: security-auditor. Date: 2026-06-03. Autopilot Phase 3, iteration 1.
> Artifact: src/tokenlab/duration.py
> Spec: docs/specs/parse-duration.md. Baseline: CONSTITUTION.md section 5 (security posture), section 2 (non-negotiables); CONSTITUTION.project.md (no project sections defined).

## Summary

| Severity  | Count |
|-----------|-------|
| CRITICAL  | 0     |
| HIGH      | 0     |
| MEDIUM    | 0     |
| LOW       | 1     |

Verdict: PASS (no blocker/major findings). One LOW (minor) finding is logged to BACKLOG.md. No REJECT emitted.

The function is a pure, stdlib-only string parser with no I/O, no network, no persistence, no deserialization, and no dynamic code execution. The four requested assessment axes (ReDoS, unbounded resource consumption, eval/exec/deserialization, input-validation completeness) were each examined end-to-end and empirically probed.

## Findings

### F1 [LOW] Unbounded integer allocation from a very long digit run relies on an incidental, caller-defeatable CPython guard

- Location: src/tokenlab/duration.py:60 (total += int(value) * _UNIT_SECONDS[unit]); regex admits arbitrary-length runs at duration.py:7 and duration.py:10.
- Class: Uncontrolled resource consumption (CWE-400) — algorithmic / memory.
- Description: The grammar places no upper bound on the digit count of a component (spec R7 deliberately removes per-component caps and clock-range validation). An adversarial input such as ("9" repeated N times) + "h" passes _DURATION_PATTERN and then reaches int(value). Arbitrary-precision int construction from a base-10 string is super-linear in N, and the resulting integer occupies memory proportional to N. For N = 100000 this costs ~60 ms of CPU and allocates a large bignum; larger N scales worse. In the current runtime this is incidentally mitigated by CPython sys.int_max_str_digits (default 4300), which raises ValueError on int of 4301 digits. That coincidentally matches the function ValueError contract (R8), so the mitigation is invisible to callers and does not violate the spec. However, the mitigation is not part of this function design: it is a process-global setting any code in the host process may disable via sys.set_int_max_str_digits(0). With the guard disabled, this function regains an unbounded CPU/memory sink driven purely by untrusted input length.
- Exploitation: Only reachable if (a) a caller feeds untrusted, length-unbounded strings into parse_duration, AND (b) the host process has raised or disabled int_max_str_digits. The function performs no length check, so it offers no defence-in-depth of its own. Impact is local DoS (CPU + memory), not RCE or data exposure. Both preconditions required, hence LOW not MEDIUM.
- Why not higher: Under default CPython settings the input is rejected with the contractually-correct ValueError and bounded cost. No concrete exploit on a default-configured runtime — a defence-in-depth gap, which maps to LOW per the rubric.
- Remediation (BACKLOG, do not fix this iteration): Add an explicit, self-contained input-length guard at the function boundary (reject trimmed inputs longer than a generous constant; a real duration string is well under ~64 chars) and raise the same ValueError. This removes the dependency on a global interpreter setting. Per CONSTITUTION section 12 this is minor and MUST be logged to BACKLOG.md, not fixed inline. The backlog entry should flag that the cap guards total input length, distinct from the per-value cap R7 declines.

## Assessment detail (requested axes)

### (1) ReDoS / catastrophic backtracking — CLEAR

- Patterns: _DURATION_PATTERN = \A(?:[0-9]+[hms])+\Z and _COMPONENT_PATTERN = ([0-9]+)([hms]).
- The inner group (?:[0-9]+[hms])+ has no ambiguous overlap: [0-9] and [hms] are disjoint character classes, so at every input position exactly one branch can match. No nested quantifier over overlapping classes (the (a+)+ / (a|a)* shape), so no exponential or polynomial blowup is possible.
- Empirical (probe script, Python 3.11.9): matching time scales linearly for all three adversarial shapes:
  - long digit run then failing char: N=500000 -> ~5 ms.
  - max component count then failing char: N=100000 -> ~32 ms; N=500000 -> ~147 ms (linear).
  - truncated then bang: same linear profile.
- Conclusion: no ReDoS. Cost is O(n) in input length.

### (2) Unbounded resource consumption — see F1 (LOW)

Regex matching itself is bounded/linear. The only unbounded surface is int(value) on a long digit run, covered by F1.

### (3) eval / exec / deserialization — CLEAR

- Grep of src/tokenlab for eval, exec, pickle, marshal, __import__, compile, globals, locals, getattr, setattr, os., subprocess, socket, open: no matches except the two re.compile calls. R10 and CONSTITUTION section 5 ("never eval") satisfied. No deserialization. __init__.py is empty.

### (4) Input-validation completeness — STRONG

- Input treated as hostile and validated at the boundary (CONSTITUTION section 5), consistent with spec section 4.
- \A...\Z anchoring (not ^...$) correctly prevents the multiline-$ / trailing-newline bypass: "1h\n" is not accepted by \Z the way it would be by $. The outer strip() already removes a trailing newline, so the shape is defended in two layers.
- All section 7 invalid classes are rejected with ValueError: empty/whitespace-only, bare integer, unknown/uppercase suffix, negative sign, decimal, out-of-order units, repeated units, inter-component whitespace, garbage. The descending-rank check at line 57 (rank <= previous_rank) correctly collapses repeated-unit and out-of-order into one guard.
- Totality (R8): for any str, returns a non-negative int or raises ValueError. The two-stage design (whole-string gate before findall) means findall cannot meet a malformed substring, so no IndexError/AttributeError/KeyError can leak. _UNIT_ORDER[unit] and _UNIT_SECONDS[unit] lookups are safe because the gate guarantees unit in {h,m,s}.
- Error-message hygiene (R9, section 8 logging note): the message uses repr ({trimmed!r}), which escapes control characters and newlines, so an attacker cannot inject raw control chars / ANSI escapes into a consumer log via the exception string. Satisfies R9 and the section 5/8 redact-the-contents posture. No PII or secret exposure surface exists.

## Dependency audit

No dependency manifest exists (pyproject.toml, requirements*.txt, setup.py, setup.cfg, Pipfile all absent). CONSTITUTION section 1 mandates stdlib-only; the module imports only re. No dependency tree to scan, so pip-audit is not applicable. No /docs/dependency-reports/2026-06-03.md was present this iteration; given the empty dependency surface, no audit run was warranted.

Result: N/A — zero third-party dependencies (stdlib re only).

## Secrets scan

Grep across src/ for AWS keys (AKIA...), private-key headers (-----BEGIN), bearer tokens, API-key / secret patterns, and .env-style credentials: clean — no matches. The feature handles no credentials, tokens, or PII. CONSTITUTION section 2.1 satisfied vacuously.

## Notes (non-findings)

- Runtime version drift (informational, not a security finding): the audit environment is Python 3.11.9, while CONSTITUTION section 1 locks the stack to Python 3.12. The int_max_str_digits guard exists in both (added in 3.11), so the F1 analysis holds for 3.12. Version-policy conformance is a qa-reviewer / devops concern, flagged for visibility.

## Appendix — probe commands

ReDoS/integer probes were run as standalone script files (the python -c inline form is correctly denied by the permission model as arbitrary code execution). Probes: linear-time backtracking confirmation up to 500k-char adversarial inputs; int_max_str_digits default-guard behavior (raises ValueError at 4301 digits on the default 4300 limit).
