---
name: autopilot
description: Run the full multi-agent pipeline autonomously from a raw requirements input. Batches user clarifications upfront, then runs spec → code → test → doc → review → release with a convergence loop, surfacing only urgent escapes or final results.
---

# /autopilot — autonomous pipeline orchestration

You are now operating in **autopilot mode**. Your role shifts from interactive router to autonomous orchestrator. Follow this playbook in order. Do NOT skip steps. Do NOT ask the user anything outside the intake window.

## Input

The slash-command argument is either:
- A path to a requirements file (e.g. `/autopilot docs/requests/new-thing.md`), or
- An inline requirements blurb (everything after `/autopilot ` is the request).

If no argument is provided, ask the user "What do you want me to build?" once, then proceed.

## Phase 0 — Backlog pre-flight (read-only, advisory)

Before opening the intake window, scan `BACKLOG.md` at the repo root (if it exists) for items past their deadline. This is a non-blocking, advisory check — its purpose is to surface tech debt before the user commits to a new feature.

1. If `BACKLOG.md` is absent, skip Phase 0 entirely.
2. If present, parse "Active entries". List every entry whose `Deadline` field is in the past relative to today's date.
3. If the count of past-deadline entries is **zero**: print one line `→ Phase 0/4: Backlog clean (N active entries, none past deadline).` and continue to Phase 1.
4. If the count is **non-zero**: print

   ```text
   → Phase 0/4: Backlog has <N> entries past deadline. Per CONSTITUTION §12.3 these will promote to `major` findings during convergence.
     Consider running `backlog-curator` BEFORE this feature to consolidate / archive / re-plan. Options:
       (a) Continue — Phase 3 will surface them as findings against this feature.
       (b) Groom first — invoke backlog-curator now, then restart autopilot.
   ```

   This is the ONLY user prompt in Phase 0. Default: (a). If the user picks (b), stop autopilot and invoke `backlog-curator` directly — autopilot does not orchestrate grooming itself.
5. Phase 0 produces no artifact and writes no state file. It is purely advisory.

## Phase 1 — Intake (single user interaction window)

This is the ONLY phase where the user is in the loop. Once you exit it, the pipeline runs to completion without further prompts unless an urgent emergency escape fires.

1. **Status line:** print `→ Phase 1/4: Intake — requirements-intake is drafting clarifying questions.`
2. Invoke `requirements-intake` in **Mode A** with the user input.
3. The agent returns either a `QUESTIONS`, a `SPLIT-REQUIRED`, or (rarely, if the request was already pristine) a `TICKET-LOCKED` block.
   - On `SPLIT-REQUIRED`: stop. Print the block to the user and ask which slice to run first. Then restart Phase 1 with that slice.
   - On `TICKET-LOCKED`: skip to Phase 2.
   - On `QUESTIONS`: continue below.
4. Convert the `QUESTIONS` block into a single `AskUserQuestion` call:
   - One question per `AskUserQuestion` question, up to 4 per call. If there are more than 4, run `AskUserQuestion` in batches but treat the WHOLE intake as one user-facing round — do not interleave with other work.
   - For each question, the proposed default appears as the FIRST option, labeled "(Default)".
   - "Other" is always offered by the tool itself for free-text answers.
5. Collect all answers. Re-invoke `requirements-intake` in **Mode B**, passing the original request, the `QUESTIONS` block, and an `ANSWERS` block:

   ```
   === ANSWERS ===
   A1: <user's answer to Q1>
   A2: <user's answer to Q2>
   ...
   === END ANSWERS ===
   ```

6. The agent returns a `TICKET-LOCKED` block pointing at `/docs/requirements/<feature>.md`. Phase 1 is complete. **No further user prompts until Phase 3.**

## Phase 2 — Autonomous build

Print `→ Phase 2/4: Build — running spec → code → test → doc, plus parallel specialists.`

Run the pipeline in this exact order. Each agent receives the **paths** to the ticket and all prior artifacts (not the file contents). Each agent reads the sections it needs from disk; never paste full file bodies into a dispatch prompt — that blows up context on every handoff. When dispatching `qa-reviewer` (in Phase 3 below), prepend `[mode: autopilot]` to the dispatch input so the agent knows it can REJECT on missing ticket/spec/doc artifacts.

### 2a. Spec

1. Invoke `spec-architect` with the ticket.
2. If it emits `CLARIFY`, dispatch to the named `TO:` agent and return the response. (At this point `TO:` is almost always intake — but intake is closed, so the orchestrator treats a non-`URGENT` CLARIFY targeted at intake as a request to use the inferred assumption documented in ticket §14. Surface only `URGENT: yes` CLARIFYs to the user — see "Emergency escape" below.)
3. Continue once the spec is on disk under `/docs/specs/`.

### 2b. Parallel specialists (only when applicable)

Determine applicability by reading the ticket and spec:
- `database-designer` — required if ticket §8 (persistence) is non-empty OR if `/migrations/` or `/docs/schema/` is mentioned in spec.
- `devops-engineer` — required if ticket implies new infra, container, CI workflow, or env var.
- `dependency-auditor` — required if spec adds a new direct dependency.

Run all applicable specialists in parallel. Their outputs feed `developer`.

### 2c. Implementation

1. Invoke `developer` with the ticket, spec, and specialist outputs.
2. Route any `CLARIFY` per the same rules as 2a.

### 2d. Tests

Invoke `test-engineer` with the ticket, spec, and `/src/` paths produced by developer. Route any REJECT to its `TO:` (usually `developer` or `spec-architect`).

### 2e. Docs

Invoke `doc-writer` once tests are green. Route any CLARIFY per the rules above.

## Phase 3 — Convergence loop

Print `→ Phase 3/4: Convergence — running reviewers until no new REJECTs surface.`

This is a fixpoint loop. It terminates when the review trio returns clean, when the no-progress detector fires, or when the iteration cap is reached.

### State persistence (read at loop start, write after each iteration)

The convergence loop is the longest-running and most interruptible phase. Persist its state to disk so a killed session can resume without re-running clean reviewers and so the no-progress detector survives a context-window compaction.

**State file:** `/docs/.autopilot-state/<feature>.json` (separate from `/docs/qa-reports/` artifacts — tool state, not user-facing reports). Schema:

```json
{
  "feature": "<slug>",
  "started_at": "<ISO-8601>",
  "status": "phase3_running" | "phase4_running" | "stalled" | "released" | "release_blocked",
  "iteration": 3,
  "signatures": {
    "a1b2c3d4": { "first_seen": 1, "last_seen": 3, "from": "qa-reviewer", "to": "developer", "severity": "blocker", "summary": "..." },
    ...
  }
}
```

Field semantics:
- `status` — which phase the orchestrator is in (`phase3_running` or `phase4_running`), or a terminal state (`stalled` on smart-cap fire, `released` on Phase 4 success, `release_blocked` on Phase 4 BLOCKED). The `status` value is the only source of truth for which phase's iteration counter applies.
- `iteration` — the iteration counter for the **current phase named by `status`**. Resets to `0` when transitioning from Phase 3 to Phase 4.
- `signatures` — REJECT signature → metadata. The `first_seen`/`last_seen` numbers are interpreted against `iteration` (the current phase's counter); when transitioning phases, the orchestrator either prefixes new signatures with the new phase context or simply starts with a fresh `signatures` map at Phase 4 (recommended, since Phase 3 and Phase 4 rejections are about different artifacts).

**At loop start:** read the state file if it exists. Resume the iteration counter and signature table for the phase named by `status`. If `status === "released"`, the prior run completed — print the prior final report and stop. If `status === "stalled"` or `status === "release_blocked"`, surface the prior escalation to the user before re-running.

**After every iteration:** atomically rewrite the state file (write to `.tmp`, rename). Never append — the file is the snapshot.

**No `iteration_totals` array.** The no-progress detector computes "did REJECT count decrease?" by comparing the current iteration's collected REJECTs against the previous iteration's, both available in-context during the loop. Persisting the totals to disk adds schema weight without enabling any check that isn't already done in memory.

### Loop body

1. **Run reviewers in parallel:**
   - `qa-reviewer` (always)
   - `code-reviewer` (always)
   - `observability-auditor` (always — constitution §8 binds every change to event-logging discipline)
   - `security-auditor` (when the spec or implementation touches auth, input, secrets, crypto, network/file I/O, deserialization, SQL, or shell — i.e. its trigger description)
   - `performance-analyst` (when the spec or implementation touches queries, loops, async, large data, or hot paths)
   - `ux-consultant` (when the implementation touches anything under `/src/components`, `/pages`, `/app`, `/styles`)
   - `dependency-auditor` (when any dependency manifest — `package.json`, `pyproject.toml`, `go.mod`, `Cargo.toml`, `Gemfile`, etc. — was modified in this iteration's fixes, OR was modified at all during Phase 2 and has not yet been audited since)

   > **Design note — parallel, not fail-fast.** Reviewers run in parallel rather than sequentially gating on `qa-reviewer`. A "qa first, others only if qa passes" design saves ~6 invocations per iteration when qa rejects, but `qa-reviewer` cannot catch what specialist reviewers catch (security flaws, perf cliffs, a11y gaps, observability gaps), so qa-pass is not equivalent to converged. Parallel-always optimizes wall time AND prevents the bug where qa approves code that security would have rejected. Do not flip this to sequential without a corresponding redesign of the reviewer trust model.

2. **Collect all REJECT blocks** from the reviewers' outputs. Reviewers emit REJECTs only for `blocker` and `major` findings. `minor` findings live in the reviewers' reports but do NOT appear as REJECTs.

3. **Extract minor findings → `BACKLOG.md` (atomic step).** Scan each reviewer's report from this iteration for `minor` / `nit` / `nice-to-have` / `LOW` findings. For each one, append a new entry to `BACKLOG.md` under "Active entries" using the format defined in CONSTITUTION §12.2. IDs are sequential — read the highest existing `B-NNN` and continue from there. This is a single write per iteration; do it BEFORE the convergence check so the backlog reflects reality even when convergence is about to close. If this iteration adds ≥5 new entries, set a flag for Phase 4 to include a tech-debt-tail warning in the release report (per CONSTITUTION §12.5).

4. **If no REJECTs:** Phase 3 has converged. Transition the state file (set `status` to `phase4_running`, reset `iteration` to `0`, clear `signatures`), write it, and continue to Phase 4 (Release).

5. **Compute REJECT signatures.** For each REJECT, the signature is:

   ```text
   sha = first-8-chars-of-sha256(FROM + TO + SEVERITY + ARTIFACT + normalized(FINDINGS))
   ```

   Where `normalized(FINDINGS)` strips whitespace and line numbers (so a re-flagged issue with shifted line numbers still hashes identically). Track signatures across iterations in the state file (see above).

6. **No-progress detector:**
   - If any signature appears in **3 consecutive iterations**, escalate (see below).
   - If the **total number of REJECTs did not decrease** from the previous iteration AND no signature changed, escalate.

7. **Iteration cap:** if `iteration ≥ 8`, escalate.

8. **Otherwise, fan out fixes:** group the REJECTs by `TO:` field, invoke each target agent in parallel with the REJECT blocks targeting it. Collect responses.

9. **Increment `iteration`, write the state file, return to step 1.**

### Escalation (smart-cap fire)

Print:

```
⚠ Convergence loop stalled at iteration N.

Recurring or unresolved findings:
  - [SEVERITY] FROM <agent> TO <agent>: <one-line summary>  (seen in iterations X, Y, Z)
  - ...

Artifacts:
  - Requirements: /docs/requirements/<feature>.md
  - Spec:         /docs/specs/<feature>.md
  - Code:         /src/...
  - Tests:        /tests/...
  - QA report:    /docs/qa-reports/<feature>-<date>.md

Recommended next step: <orchestrator's best guess at what the user needs to decide>
```

Then **stop**. Wait for user input. This is the second user-interaction window of the entire autopilot run.

## Phase 4 — Release

Print `→ Phase 4/4: Release — running release-engineer to take the approved change from green CI to verified-running.`

Phase 4 begins ONLY after Phase 3 converges clean (no REJECTs from qa-reviewer or any other reviewer). State file `status` transitions from `phase3_running` to `phase4_running`; the iteration counter resets. Constitution §2.7 ("no deploy without observability + rollback") and §9 (Definition of Done) are binding — the run is not complete until release-engineer has either marked the release `RELEASED` or surfaced a `BLOCKED` reason the user must resolve.

### 4a. Invoke release-engineer

Invoke `release-engineer` once, with the full artifact bundle:

- `/docs/requirements/<feature>.md`
- `/docs/specs/<feature>.md`
- `/src/` (paths produced by developer)
- `/tests/` (paths produced by test-engineer)
- `/docs/qa-reports/<feature>-<date>.md` (qa-reviewer APPROVED verdict)
- `/docs/security-reports/<feature>-<date>.md` (if security-auditor ran)
- `/docs/observability-reports/<feature>-<date>.md` (observability-auditor — always present after Phase 3)

**Multi-day convergence — date resolution.** When Phase 3 runs across calendar days, an agent (qa-reviewer, observability-auditor, etc.) may produce multiple dated reports for the same feature (e.g. `<feature>-2026-06-01.md` AND `<feature>-2026-06-02.md`). In that case the orchestrator MUST pass the **most-recent-by-mtime** file for each artifact type to release-engineer. Older dated files are kept on disk as audit trail; release-engineer reads only the latest. Same rule applies for any subsequent re-entry to Phase 3 that produces new dated reports.

The agent will execute its five gates in order: source-control hygiene → CI green → deploy executed → smoke test passes → observability footprint live. Its final artifact is `/docs/release-reports/<feature>-<YYYY-MM-DD>.md` with verdict `RELEASED` or `BLOCKED`.

### 4b. Route REJECTs from release-engineer

Release-engineer's REJECTs identify which earlier agent owns the gap that blocks shipping. Route them automatically:

- **CI test failure** → `TO: developer` (impl bug) or `TO: test-engineer` (flaky test). Re-invoke the named agent with the REJECT. After their fix, re-enter **Phase 3** (convergence loop) — not Phase 4 — because new code requires the full reviewer trio again. Once Phase 3 re-converges, return to step 4a.
- **CI pipeline-config failure** (workflow YAML error, missing step, bad runner image) → `TO: devops-engineer`. After their fix, re-invoke release-engineer directly; no Phase 3 re-entry needed because no production code changed.
- **Missing deploy mechanism** → `TO: devops-engineer`. The agent writes the workflow/manifests/Makefile target. After they finish, re-invoke release-engineer.
- **Smoke test fails post-deploy** → release-engineer is instructed to **execute the documented rollback FIRST**, then REJECT to `TO: developer` with the captured response and rollback verification. After developer fixes, re-enter Phase 3.
- **Missing log store / metrics infra / alert rule** → `TO: devops-engineer`. After their fix, re-invoke release-engineer.
- **Missing rollback path for a destructive schema change** → `TO: database-designer`. After their fix, re-invoke release-engineer.

Track release-engineer's REJECTs with the same signature mechanism as Phase 3 (sha256 of FROM+TO+SEVERITY+ARTIFACT+normalized(FINDINGS)) and write them into the state file's `signatures` map. The `iteration` counter increments per release attempt. The no-progress detector and 8-iteration cap apply to Phase 4 the same way they apply to Phase 3: if release-engineer rejects the same signature three times in a row, or if `iteration ≥ 8`, escalate to the user.

### 4c. URGENT BLOCKED CLARIFY (production-deploy approval, missing credentials, etc.)

Release-engineer emits a `CLARIFY` with `BLOCKED: yes` and `URGENT: yes` only when it cannot proceed without a user decision that no upstream agent can make. The two common cases:

1. **Production deploy needs interactive approval.** The deploy command is documented but requires a human "yes" (e.g. `flyctl deploy --prod` prompting, a CI manual-approval gate). Surface this via `AskUserQuestion`:
   - Question: "Production deploy for `<feature>` is staged. The deploy mechanism requires interactive approval. Run it now?"
   - Options: "Yes — deploy now (Default)", "No — stop here, I'll deploy manually later".
2. **No deploy mechanism exists for the target environment.** Release-engineer has written `/docs/release-reports/<feature>-deploy-runbook.md` documenting what's missing. Surface via `AskUserQuestion`:
   - Question: "No automated deploy path exists for `<target>`. Release-engineer wrote a manual runbook at `<path>`. How do you want to proceed?"
   - Options: "Pause autopilot here — I'll deploy manually (Default)", "Route to devops-engineer to author a deploy workflow now".

Each URGENT CLARIFY is a separate `AskUserQuestion` call — do NOT batch them with prior intake or Phase 3 escalation questions; the intake-closed rule for Phase 2 does not apply once Phase 4 has begun, but each question must still be one decision in one call.

After the user answers, return the answer to release-engineer and continue. If the user picks "deploy manually later", the autopilot run ends with verdict `STAGED — manual deploy pending`; print the final report (next section) with that note.

### 4d. Final report — RELEASED verdict (success path)

When release-engineer returns with `RELEASED`, set the state file `status` to `released`, write it, and print the canonical final report:

```
✓ Autopilot complete (Phase 3 in N convergence iterations, Phase 4 in M release iterations).

Built:
  - <one-line description from the ticket>

Artifacts:
  - Requirements: /docs/requirements/<feature>.md
  - Spec:         /docs/specs/<feature>.md
  - Code:         <count> files under /src/
  - Tests:        <count> files, <X> tests passing
  - Docs:         README + /docs/api/<feature>.md
  - QA verdict:   APPROVED (see /docs/qa-reports/<feature>-<date>.md)

Specialist reports:
  - <list any of: security-reports, perf-reports, code-reviews, ux-reviews, dependency-reports, observability-reports>

Release:
  - Branch:        <branch-name>
  - PR:            <url>
  - CI status:     green
  - Deploy target: <staging | production>
  - Deploy result: <one-line>
  - Smoke test:    PASS — <command> → <expected==actual>
  - Observability: <N>/<N> spec events verified live; alerts registered with runbooks
  - Rollback plan: /docs/release-reports/<feature>-<date>.md §Rollback plan

Notable inferred assumptions (review for accuracy):
  - <pull from ticket §14, only items the spec or code actually relied on>
```

### 4f — Merge the PR (gated by CONSTITUTION §14)

Whether the orchestrator merges the PR to `main` after a `RELEASED` verdict is governed by the effective autonomy level (see CLAUDE.md "Workflow autonomy" — read CONSTITUTION §14.2, or `CLAUDE.project.md` when no `CONSTITUTION.md` exists, and apply any stricter personal override). The §14.1 floor always holds: green CI is required, and `main` is reached only by merging the PR — never a direct push.

- **`review-all`:** do NOT merge. Leave the PR open and end the report with "PR ready to merge — awaiting your approval".
- **`review-critical`:** merge (squash) automatically UNLESS this feature is a critical change per §14.4 (touched a schema migration, a public API contract, the security-sensitive set, or added a direct dependency) — then leave it open for human review like `review-all`.
- **`autonomous`:** delegate the merge to `release-engineer` (squash) once CI is green, then delete the merged branch (remote + local).

When the orchestrator does not merge, say so explicitly in the final report so the user knows the PR is waiting.

### Memory review

Before closing, scan the run for content worth persisting across sessions:

1. **Add** a `project` memory for any significant decision, constraint, architectural choice, or blocked approach discovered during this run that is not already captured and not derivable from reading the code.
2. **Add** a `reference` memory for any external resource (dashboard URL, Linear project, runbook path) newly referenced during the run.
3. **Remove or update** any existing memory that this run has made stale — a decision reversed, a provider swapped out, a constraint lifted.

Write new memories to `~/.claude/projects/<project>/memory/` (for `user`/`feedback` types) or `.claude/memory/` in the repo (for `project`/`reference` types) per the memory system rules in `CLAUDE.md`. Update the relevant `MEMORY.md` index. Do not ask the user — this is a mandatory closing step, not optional housekeeping.

Then stop. The autopilot run is complete.

### 4e. Final report — BLOCKED verdict

When release-engineer returns with `BLOCKED` (CI red after smart-cap exhaustion, smoke test fails after rollback, missing deploy mechanism the user chose not to author, etc.), set the state file `status` to `release_blocked`, write it, and print:

```
⚠ Autopilot blocked at release (Phase 3 converged in N iterations; Phase 4 blocked after M iterations).

Built (Phase 3 complete):
  - <one-line description from the ticket>

Artifacts:
  - Requirements: /docs/requirements/<feature>.md
  - Spec:         /docs/specs/<feature>.md
  - Code:         <count> files under /src/
  - Tests:        <count> files, <X> tests passing
  - QA verdict:   APPROVED (see /docs/qa-reports/<feature>-<date>.md)

Release blocker:
  - Reason:       <one-line from release-engineer's report>
  - Owns the gap: <agent name: developer / test-engineer / devops-engineer / database-designer>
  - Release report: /docs/release-reports/<feature>-<date>.md (verdict: BLOCKED)

Recommended next step: <orchestrator's best guess at what the user needs to decide>
  - Examples:
      "Approve a manual deploy via the runbook at <path>."
      "Authorize devops-engineer to author the missing deploy workflow."
      "Investigate the smoke-test failure captured in the release report."
```

Before closing, scan the run for content worth persisting across sessions:

1. **Add** a `project` memory for any significant decision, constraint, architectural choice, or blocked approach discovered during this run that is not already captured and not derivable from reading the code.
2. **Add** a `reference` memory for any external resource (dashboard URL, Linear project, runbook path) newly referenced during the run.
3. **Remove or update** any existing memory that this run has made stale — a decision reversed, a provider swapped out, a constraint lifted.

Write new memories to `~/.claude/projects/<project>/memory/` (for `user`/`feedback` types) or `.claude/memory/` in the repo (for `project`/`reference` types) per the memory system rules in `CLAUDE.md`. Update the relevant `MEMORY.md` index. Do not ask the user — this is a mandatory closing step, not optional housekeeping.

Then stop. The user resolves the gap; a subsequent `/autopilot` resume picks up from `status: release_blocked` and re-enters Phase 4.

## Emergency escape (mid-pipeline)

Any agent at any stage may emit an `URGENT: yes` field in a `CLARIFY` block. The orchestrator surfaces these to the user immediately, regardless of the intake-closed rule.

Criteria for an emergency CLARIFY (the agent is instructed in its own definition to be conservative here):
- A required user decision that intake could not have anticipated (e.g. a regulatory question discovered only when reading the spec).
- A constitution conflict that requires §11 amendment.
- A discovered conflict with existing production code that changes the project's scope.

The orchestrator surfaces the `QUESTIONS` block via `AskUserQuestion`, returns the answers to the emitting agent, then resumes the pipeline at the same point.

## Anti-patterns (do NOT do these)

- Do NOT ask the user questions outside the intake window or an explicit emergency escape.
- Do NOT skip the convergence loop because "it looks fine." Even one reviewer rejection means another iteration.
- Do NOT mark the run successful while any REJECT remains unresolved.
- Do NOT exceed 8 convergence iterations. If you're at 8, escalate — burning more iterations rarely converges.
- Do NOT silently drop CLARIFY blocks. Every one is either auto-routed to its `TO:` or, if `URGENT`, surfaced to the user.
- Do NOT bypass `requirements-intake` even when the user's request looks complete. A skipped intake is the most common reason autopilot loops fail to converge later.
- Do NOT batch user questions outside the intake window. The whole point of intake is to amortize human latency.
