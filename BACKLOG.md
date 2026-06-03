# agent-forge — Backlog

Tech debt, deferred fixes, and known cleanup items for the **scaffold itself**. Per CLAUDE.project.md, backlog discipline (CONSTITUTION §12) applies to agent-forge meta-work: minor findings about the scaffold land here as numbered entries rather than as informal "I'll get to it" promises in chat. Singletons are fine — `backlog-curator` finds the cross-session patterns.

This file is the forge-development ledger. It is **not** inherited by downstream products: `/init-project` Step 13 writes a fresh, empty `BACKLOG.md` at bootstrap, so these forge-internal entries never travel into a product repo.

## How this file works

- **Findings land here, not in feature/scaffold PRs as inline fixes.** A minor finding gets a numbered entry; the fix happens later as its own focused change.
- **IDs are sequential, never reused.** `B-001`, `B-002`, … in order. Closed entries move to "Closed entries" below; do not renumber.
- **Take an item:** invoke `refactor-specialist B-NNN` for behavior-preserving cleanup, or make the change as a normal scaffold edit (with version bump + UPGRADING entry per CLAUDE.project.md) for anything that touches forge-owned files.
- **Deadlines are real.** Default 90 days from Created. Past-deadline entries promote to `major` on the next grooming/pipeline pass.

## Active entries

<!-- None currently. Reviewers and meta-work findings append here. -->

## Closed entries (audit trail — one release cycle)

## B-001 — `/forge-update` is inconsistent about whether it owns `CLAUDE.project.md`

- **Created:** 2026-06-02
- **Source:** orchestrator finding during the v1.11.0 documentation-sync pass
- **Type:** docs
- **Severity:** minor (singleton)
- **Suggested fix:** Four places disagree on the ownership/handling of `CLAUDE.project.md`. Decide the intended behavior first, then reconcile all references:
  - [.claude/commands/forge-update.md:19](.claude/commands/forge-update.md#L19) lists `CLAUDE.project.md` under "Will update (forge-owned)" with a "(see note below)" pointer.
  - [.claude/commands/forge-update.md:51](.claude/commands/forge-update.md#L51) (Option-A scoped diff) only diffs `.claude/agents/ .claude/commands/ .claude/templates/` — `CLAUDE.project.md` is excluded from the actual diff scope.
  - [docs/getting-started.md](docs/getting-started.md) forge-owned table lists `CLAUDE.project.md` in the **"Project-owned (never touched)"** column.
  - The "(see note below)" reference at line 19 appears to be dangling (no matching note was found in the file's update section).
  - Tension also exists with `CLAUDE.md`'s framing that `/forge-update` overwrites `CLAUDE.md` *without losing project-specific additions* — which implies `CLAUDE.project.md` is preserved (project-owned), contradicting line 19. Resolve toward project-owned-and-preserved unless there's a deliberate reason otherwise, then fix the table cell, the diff scope, line 19, and add/remove the note. Touches a command file → version bump + UPGRADING entry.
- **Deadline:** 2026-08-31
- **Closed:** 2026-06-02 (forge v1.11.1). Investigation found it was bigger than logged: `forge-update.md` had `CLAUDE.md` and `CLAUDE.project.md` ownership **backwards** vs. the documented design. Resolved to: `CLAUDE.md` forge-owned/updated, `CLAUDE.project.md` project-owned/never-touched (matching `CLAUDE.md`'s own text and `getting-started.md`). Corrected across frontmatter, will-update/never-touch lists, Step 1 diff scope, Step 4 apply, and Forbidden actions; dangling "(see note below)" removed. `docs/` already agreed, so no doc edits.

## B-002 — Confirm `/init-project` overwrites (not skips) project-owned ledgers at bootstrap

- **Created:** 2026-06-02
- **Source:** orchestrator finding during the v1.11.0 documentation-sync pass
- **Type:** cleanup
- **Severity:** minor (singleton)
- **Suggested fix:** [init-project.md:185](.claude/commands/init-project.md#L185) Step 13 says "Create a file named `BACKLOG.md` ... with this exact content", which *reads* as an unconditional write but is not explicit about the create-if-absent vs. overwrite-if-present case. This is the mechanism that prevents the forge's own `BACKLOG.md` from leaking into a downstream product, so it must reliably reset. Make the overwrite-on-bootstrap behavior explicit in Step 13, and verify the same for `CHANGELOG.md` and the `CONSTITUTION.project.md` stub. If init-project is meant to be idempotent and refuses to re-run on an already-bootstrapped repo, document how a fresh template clone (which may ship these files) is distinguished from a bootstrapped one.
- **Deadline:** 2026-08-31
- **Closed:** 2026-06-02 (forge v1.11.1). Step 6 now deletes `docs/task-flows.md` (a forge doc previously left behind in products). Added an explicit file-creation policy for steps 10–16: overwrite forge-shipped `CLAUDE.project.md`/`BACKLOG.md` on a fresh clone (prevents leakage), preserve `CLAUDE.project.md`/`CONSTITUTION.project.md`/`CONTRIBUTING.md`/`BACKLOG.md`/`CHANGELOG.md` on a confirmed re-run (prevents data loss).

<!-- Archive entries older than one release cycle. -->
