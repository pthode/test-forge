# Release Report — parse-duration

> Project: `tokenlab` · Date: 2026-06-03 · Autopilot Phase 4 (release-engineer)
> Sources: `/docs/requirements/parse-duration.md`, `/docs/specs/parse-duration.md`,
> `/docs/qa-reports/parse-duration-2026-06-03.md` (APPROVED),
> `/docs/security-reports/parse-duration-2026-06-03.md`,
> `/docs/observability-reports/parse-duration-2026-06-03.md`,
> `/CONSTITUTION.md` (§1, §8, §9, §10, §13), `/CONSTITUTION.project.md` (no §P sections).

- **Branch:** _not yet created — release HALTED at Gate 2 (see below)_
- **PR:** _not yet opened_
- **CI status:** **ABSENT — no workflow under `/.github/workflows/`** (BLOCKER)
- **Deploy target:** N/A — importable library module (CONSTITUTION §1)
- **Deploy command:** N/A (no runtime service to deploy)
- **Deploy result:** N/A

## Gate-by-gate result

| # | Gate | Result | Notes |
|---|------|--------|-------|
| 0 | §13 version bump / changelog | **SKIPPED (correct)** | §13.1 scheme = `none`; §13.3 says CHANGELOG.md is not maintained. No version bump, no tag, no changelog edit. |
| 1 | Source-control hygiene | **BLOCKED (precondition)** | See "Source-control hygiene" below — the working tree mixes the parse-duration feature with the entire `/init-project` bootstrap; needs a separation decision before a clean single-concern branch (§10) can be cut. |
| 2 | CI green | **REJECT → devops-engineer** | No CI workflow exists. §9 DoD requires the suite green "locally **and in CI**". 82 tests pass locally (insufficient on its own). |
| 3 | Deploy executed / staged | **N/A (correct)** | §1 deployment target is "N/A — importable library module." No staging/production environment exists; nothing to deploy. Not a fabricated gap. |
| 4 | Production smoke test | **N/A (deferred)** | No deployment surface (Gate 3 N/A). Library-level "smoke" = the public-import + R1 happy path, exercisable only once CI runs it. See below. |
| 5 | Observability footprint live | **VACUOUS PASS** | §8a satisfied vacuously per observability report (pure primitive, no log line, no events/alerts). No log store to query because there are no events. Confirmed against `/docs/observability-reports/parse-duration-2026-06-03.md`. |

The release **cannot reach `RELEASED`** while Gate 2 is red: §9 DoD makes "green in CI" a binding
Definition-of-Done item, and the project has no CI pipeline at all. I will not fabricate a workflow
(forbidden — surface the gap, do not paper over it); authoring it is `devops-engineer`'s gate.

## Gate 1 — Source-control hygiene (precondition not yet met)

The current working tree is on `main` and is **not** a clean single-concern feature change. `git status` shows the parse-duration feature commingled with the entire project bootstrap:

- **Feature files (parse-duration):** `src/tokenlab/` (new), `tests/` (new), `conftest.py` (new), `README.md` (modified — usage entry), and the feature's report artifacts under `docs/specs/`, `docs/requirements/`, `docs/qa-reports/`, `docs/security-reports/`, `docs/perf-reports/`, `docs/code-reviews/`, `docs/observability-reports/`.
- **Bootstrap / scaffold files (NOT this feature):** `CONSTITUTION.md` (new), `CONSTITUTION.project.md` (new), `CONTRIBUTING.md` (new), deleted `CONSTITUTION.template.md`, deleted `docs/*.md` manual pages (README, audit-prompt, constitution, customizing, getting-started, how-it-works, intent, task-flows, troubleshooting), modified `CLAUDE.md` / `CLAUDE.project.md`, modified `BACKLOG.md`, plus `docs/.autopilot-state/` and `__pycache__/`.

Per CONSTITUTION §10 ("One concern per PR"), the parse-duration feature branch must NOT carry the
whole `/init-project` bootstrap. That commingling is a design decision the user owns, not something
I should silently force into a `feat/parse-duration` branch. Recommended resolution once Gate 2 is
unblocked: land the bootstrap (constitution, scaffold deletions, CLAUDE edits) as its own commit/PR
first, then branch `feat/parse-duration` from the resulting `main` carrying only the feature files
+ feature reports. `__pycache__/` should be git-ignored, not committed.

## Smoke test (planned — to run in CI once Gate 2 lands)

For a stdlib library there is no deployed endpoint; the equivalent of a production smoke test is the
public-surface import + the spec's primary happy path (R1/R2), run in the CI environment:

- **Command:** `python -c "from tokenlab.duration import parse_duration; assert parse_duration('1h30m') == 5400; print('smoke ok')"`
- **Expected:** prints `smoke ok`, exit 0.
- **Actual (local pre-CI dry run):** PASS — see "Local verification" below. Not yet exercised in CI.
- **Verdict:** PASS locally; **deferred** — must be green in CI (Gate 2) to count toward DoD.

## Local verification (informational — NOT a substitute for CI per §9)

- `python -m pytest -q` → **82 passed in 0.15s**.
- Local interpreter: **Python 3.11.9**. NOTE: CONSTITUTION §1 pins **Python 3.12**. The CI workflow
  authored for Gate 2 MUST run on 3.12 so the DoD "green in CI" check is against the constitutional
  runtime, not the local 3.11.9 box. (Tests pass on 3.11.9, but CI is the source of truth.)

## Observability verification (Gate 5)

| Event name | Query | First seen |
|------------|-------|------------|
| _(none)_ | n/a — no events emitted; pure primitive, §8a satisfied vacuously | n/a |

No log/metrics store is wired up because the feature emits no events (confirmed by
`/docs/observability-reports/parse-duration-2026-06-03.md`, verdict APPROVED, 0 findings). This is
the correct reading of §8a for a pure computation, not a missing-log-store BLOCKED condition.

## Alert rules registered (Gate 5)

- None — no failure mode requires an operator-visible signal from a pure primitive (per observability report). No missing-runbook condition possible.

## Rollback plan

Trivial and fully supported by source control — the feature is a single additive, side-effect-free
pure module with no schema, no migration, no infra, and no deployed artifact:

- **Before merge:** abandon the branch / close the PR. Nothing has shipped.
- **After merge:** `git revert <merge-commit-sha>` on a new branch → PR → merge. This removes
  `src/tokenlab/duration.py`, the `tests/`, and the README usage entry. No data migration, no
  re-deploy, no cache invalidation — the module simply ceases to exist for importers.
- **Tested?** The revert path is exercisable as a pure `git revert` with zero runtime side effects;
  there is no destructive operation to undo. No untested-rollback waiver is required.

## Tech-debt note (CONSTITUTION §12.5)

Phase 3 filed 5 minor findings to `BACKLOG.md` (no blocker/major). §12.5 threshold is "≥5 new
backlog entries in one iteration" — this run is AT the threshold. The user should consider whether
to schedule a burndown pass before the next feature.

## Verdict

**BLOCKED — Gate 2 (CI green) cannot be satisfied: no CI pipeline exists, and CONSTITUTION §9 DoD
makes "green in CI" binding (local pytest is explicitly insufficient).** Routed as a REJECT to
`devops-engineer` to author a stdlib-only pytest workflow on Python 3.12. Gates 3/4 are a legitimate
N/A (library, no deploy target per §1); Gate 5 is vacuously satisfied; Gate 1 has an unresolved
single-concern-PR separation the user should rule on. Re-run release once CI exists and is green.
