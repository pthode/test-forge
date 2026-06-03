# Upgrading agent-forge

Each entry documents one version bump. For each version, run `/forge-update` in your project
(or apply manually if you don't have a git remote pointing at agent-forge):

- **Auto-applied by `/forge-update`:** changes to `.claude/agents/`, `.claude/commands/`, `.claude/templates/`
- **Manual steps:** changes to your project's `CONSTITUTION.md` — these require human judgment and are never auto-applied
- **Verify:** checklist to confirm the upgrade landed correctly

Two optional fields gate the update when a version needs them (since v1.13.0):

- **`Requires (preflight)`:** machine-checkable prerequisites the forge code at
  that version assumes are already present in the project (e.g. a
  `CONSTITUTION.md` section added by an earlier manual step). Each item is a
  self-contained `<file> must contain <pattern> — <why + remediation>`
  assertion. `/forge-update` Step 3.5a Greps the project for each and **blocks
  apply** if any is missing — regardless of which version the project is coming
  from. Declare a `Requires` on every version whose forge-owned code depends on
  a project-owned prerequisite, re-declaring inherited ones, so a project
  arriving from below the introducing version is still caught.
- **`⚠ BREAKING`:** marks a version that crosses a MAJOR boundary. `/forge-update`
  Step 3.5b **hard-stops** and requires explicit, version-naming confirmation
  that the referenced `docs/migrations/v<x>.0.0-<name>.md` guide has been read
  before apply proceeds.

---

## 1.12.0 → 1.13.0 (2026-06-02)

### 1.13.0 — What changed

Breaking-change safety for `/forge-update`. Until now the upgrade path treated every
version bump identically: walk the `UPGRADING.md` interval, print Manual steps + Verify
checklists, overwrite the forge-owned files. Both safety nets were **advisory** — printed
for a human, never enforced — so a newer agent that assumed a project-owned prerequisite
(a `CONSTITUTION.md` section introduced by an earlier *manual* step) could be applied onto
a project that never did that step. The mismatch then surfaced as a runtime CLARIFY/blocker
instead of at update time. The gap was sharpest for a project upgrading from *below* the
version that introduced the prerequisite while skipping the version range that declared it.

v1.13.0 adds a **preflight gate** (`/forge-update` Step 3.5) with two mechanisms:

- **`Requires (preflight)` assertions (Step 3.5a).** A version entry may declare
  machine-checkable prerequisites — `<file> must contain <pattern>` — stating what its
  forge code needs present in the project *right now*. `/forge-update` Greps the project for
  each before apply and **blocks** on any miss, naming the version that declared it and the
  remediation. Assertions are self-contained (they don't reference when the prerequisite was
  added) and are re-declared on every dependent version, so a project arriving from any prior
  version is checked against what the target code actually needs.
- **`⚠ BREAKING` marker (Step 3.5b).** A version crossing a MAJOR boundary is flagged;
  `/forge-update` **hard-stops** and requires explicit, version-naming confirmation that the
  referenced migration guide was read before apply proceeds. A plain "yes" to the diff is not
  enough.

The semver model in `CLAUDE.project.md` now documents both fields as the concrete mechanism
behind "MAJOR = breaking" — previously only a convention ("write a migration guide") with no
enforcement.

This is backwards-compatible: no existing version entry carries either field, so the gate is
a no-op until a future breaking version uses it. Existing projects are unaffected.

### 1.13.0 — Forge-owned file changes (auto-applied by `/forge-update`)

- `.claude/commands/forge-update.md` — new Step 3.5 (preflight requirement gate + breaking-change hard-stop + apply confirmation moved here from Step 3); two new Forbidden actions.

### 1.13.0 — Non-forge-owned changes (manual review)

- `UPGRADING.md` — header documents the two new optional entry fields (`Requires (preflight)`, `⚠ BREAKING`).
- `CLAUDE.project.md` (agent-forge-internal) — semver model's MAJOR row documents the `⚠ BREAKING` + `Requires` convention.
- `docs/getting-started.md` — "Updating the scaffold" notes the preflight gate. (Forge-repo manual; not auto-propagated.)

### 1.13.0 — Requires (preflight)

None. This version's forge code adds no new project-owned prerequisite.

### 1.13.0 — Manual steps for existing `CONSTITUTION.md`

None. The new gate is a pure addition to `/forge-update`; no `CONSTITUTION.md` change is required.

### 1.13.0 — Verify

- [ ] Check `.forge-version` — should read `1.13.0`.
- [ ] `.claude/commands/forge-update.md` has a "Step 3.5 — Preflight" section with 3.5a/3.5b/3.5c.
- [ ] The apply confirmation ("Apply these changes?") now lives in Step 3.5c, not Step 3.
- [ ] Forbidden actions list blocking on an unmet `Requires` assertion and on an unconfirmed `⚠ BREAKING` boundary.

---

## 1.11.1 → 1.12.0 (2026-06-02)

### 1.12.0 — What changed

New **CONSTITUTION §14 "Workflow autonomy"** — a configurable, layered policy for how much of the `commit → push → PR → merge` path the orchestrator drives on its own versus pausing for human review. Previously this was hardcoded (everything human-gated, plus the branch-push model) with no project-level knob.

- **§14 is layered like the permission model.** A fixed **floor** (§14.1) that no setting can lower — protected branches PR-only, permission model intact, green CI before merge, security-sensitive changes always human-confirmed, `URGENT` always surfaces — plus a configurable **level** (§14.2): `review-all` / `review-critical` / `autonomous` (§14.3). "Critical" is defined in §14.4 (security-sensitive set, schema migrations, public API contracts, new dependencies). A per-machine **personal override** (§14.5) may only be *stricter* than the project level.
- **`/init-project` asks one new autonomy question** (new Step 17) and fills §14.2. Default for new projects is `review-all` — identical to today's behavior, so nothing changes unless a project opts into more autonomy.
- **`CLAUDE.md` gained a "Workflow autonomy" section** that computes the effective level (stricter of project §14.2 and personal override) and gates commit/push/PR/merge accordingly. The "Committing without being asked" anti-pattern is now explicitly the `review-all` default, with higher levels documented.
- **`/autopilot` Phase 4 merge is gated** by the effective level (new §4f): `review-all` leaves the PR open, `review-critical` auto-merges non-critical features, `autonomous` merges within the floor.
- **Off-by-one cleanup:** now that §14 exists, the forge-owned range is §1–§14 (was §1–§13) and future-addition examples are §15, §16, … (was §14, §15, …), updated across CLAUDE.md, the template §11, and the docs.

### 1.12.0 — Forge-owned file changes (auto-applied by `/forge-update`)

- `CLAUDE.md` — new "Workflow autonomy (CONSTITUTION §14)" section; "Committing without being asked" anti-pattern now §14-gated; §1–§14 range refs.
- `.claude/commands/init-project.md` — new Step 17 (autonomy question), checklist renumbered to Step 18; §1–§14 range refs in the `CONSTITUTION.project.md` stub.
- `.claude/commands/autopilot.md` — new Phase 4 §4f (merge gated by effective autonomy level).

### 1.12.0 — Non-forge-owned changes (manual review)

- `CONSTITUTION.template.md` — new §14; §11 range refs updated to §1–§14. See manual steps below.
- `docs/*.md` — `constitution.md`, `how-it-works.md`, `task-flows.md`, `customizing.md` document §14. (Forge-repo manual; not auto-propagated.)
- `CLAUDE.project.md` (agent-forge-internal) — declares the forge's own meta-work autonomy as `autonomous`; not relevant to downstream projects.

### 1.12.0 — Manual steps for existing `CONSTITUTION.md`

Adding §14 is **recommended but not required** — an existing `CONSTITUTION.md` with no §14 makes the orchestrator behave as `review-all` (today's behavior). To opt in:

1. Copy the `## 14. Workflow autonomy` section from `CONSTITUTION.template.md` into your `CONSTITUTION.md` (just above the Revision log).
2. Set §14.2 `Level` to `review-all` / `review-critical` / `autonomous` and change `[scope: TBD]` to `[scope: set]`.
3. Optionally record a stricter personal override per §14.5.

See [`docs/migrations/v1.12.0-workflow-autonomy.md`](docs/migrations/v1.12.0-workflow-autonomy.md).

### 1.12.0 — Verify

- [ ] Check `.forge-version` — should read `1.12.0`.
- [ ] `CONSTITUTION.md` has a §14 (or you've consciously left it at the `review-all` default).
- [ ] `CLAUDE.md` has a "Workflow autonomy (CONSTITUTION §14)" section.
- [ ] A commit/PR/merge during a run respects your chosen level (e.g. at `review-all`, the orchestrator pauses before merging).

---

## 1.11.0 → 1.11.1 (2026-06-02)

### 1.11.1 — What changed

Backlog burndown: resolves B-001 and B-002 from the forge's own `BACKLOG.md`.
Both were drift in the two slash commands.

**B-001 — `/forge-update` had `CLAUDE.md` and `CLAUDE.project.md` ownership backwards.** The command listed `CLAUDE.project.md` as forge-updated (with a dangling "see note below") and `CLAUDE.md` as "never touch / migrate manually" — the exact inverse of the documented design. `CLAUDE.md`'s own text and `docs/getting-started.md` both say the opposite: `/forge-update` overwrites `CLAUDE.md` (forge-owned) precisely *because* project additions live in `CLAUDE.project.md` (preserved). `forge-update.md` is now corrected to match:

- `CLAUDE.md` moved to **Will update (forge-owned)**; added to the Step 1 diff scope and the Step 4 apply commands.
- `CLAUDE.project.md` moved to **Will never touch (project-owned)**; added to Forbidden actions alongside `CONSTITUTION.project.md`. The dangling "(see note below)" is gone.

**B-002 — `/init-project` could leak forge-internal files into a product, and could wipe a real project's ledgers on re-run.** Two fixes:

- Step 6 (forge-doc cleanup) now also deletes `docs/task-flows.md` (added in v1.11.0; previously left behind in bootstrapped products).
- A new **file-creation policy** governs steps 10–16: on a *fresh template clone*, project-owned files are written unconditionally (replacing the forge's own shipped `CLAUDE.project.md` and `BACKLOG.md`, so forge-internal content can't leak in); on a *confirmed re-run* of an already-bootstrapped project, existing `CLAUDE.project.md` / `CONSTITUTION.project.md` / `CONTRIBUTING.md` / `BACKLOG.md` / `CHANGELOG.md` are preserved (no data loss).

### 1.11.1 — Behavior change (read this)

`/forge-update` now **updates `CLAUDE.md`**, which the broken command previously skipped. For correctly-structured projects (custom router rules in `CLAUDE.project.md`) this is exactly the intended behavior and nothing breaks. **If you have hand-edited `CLAUDE.md` directly** — against the documented design — your next `/forge-update` will overwrite those edits. Move them to `CLAUDE.project.md` first (see Manual steps).

### 1.11.1 — Forge-owned file changes (auto-applied by `/forge-update`)

- `.claude/commands/forge-update.md` — `CLAUDE.md` / `CLAUDE.project.md` ownership corrected across frontmatter, the will-update / will-never-touch lists, Step 1 diff scope, Step 4 apply commands, and Forbidden actions.
- `.claude/commands/init-project.md` — Step 6 deletes `docs/task-flows.md`; new file-creation policy for steps 10–16; pointers on steps 10 and 13.

### 1.11.1 — Manual steps for existing `CONSTITUTION.md`

None for `CONSTITUTION.md`. **One heads-up for `CLAUDE.md`:** if you previously hand-edited `CLAUDE.md` with project-specific instructions, move those edits into `CLAUDE.project.md` before your next `/forge-update`. `CLAUDE.md` imports `CLAUDE.project.md` automatically, so the behavior is identical — but only `CLAUDE.project.md` survives a forge update.

### 1.11.1 — Verify

- [ ] Check `.forge-version` — should read `1.11.1`.
- [ ] `.claude/commands/forge-update.md` lists `CLAUDE.md` under "Will update" and `CLAUDE.project.md` under "Will never touch".
- [ ] `.claude/commands/init-project.md` Step 6 deletes `docs/task-flows.md`.
- [ ] No project-specific instructions remain in your `CLAUDE.md` (they belong in `CLAUDE.project.md`).

---

## 1.10.0 → 1.11.0 (2026-06-02)

### 1.11.0 — What changed

Documentation sync + drift hardening. The `docs/` manual had fallen behind the
scaffold: it still described **16 agents** (there are 17 — `backlog-curator`
landed in v1.8.0 and was never added to the manual), `docs/constitution.md`
documented only §1–§11 (missing §12 backlog, §13 versioning, the §11.1/§11.2
split, and the `CONSTITUTION.project.md` dual-file model from v1.10.0), and
`docs/customizing.md` actively instructed the anti-pattern §11.2 was created to
prevent (adding bare `§N` sections to `CONSTITUTION.md` instead of `§P` sections
to `CONSTITUTION.project.md`). This release corrects all of that, adds a new
manual page tracing task flows, and closes the process gap that let the drift
accumulate.

- **New manual page `docs/task-flows.md`.** Sequence diagrams (Mermaid) for six
  task types — autopilot feature, bug fix with regression test, schema change,
  refactor, security-sensitive config change, backlog grooming — showing the
  agent handoffs and the CLARIFY/REJECT bounces. Added to the `docs/README.md`
  reading order (now 8 files).
- **Agent count corrected 16 → 17** across `README.md`, `how-it-works.md`,
  `intent.md`, `getting-started.md`, `audit-prompt.md`.
- **`backlog-curator` documented** in `how-it-works.md` (agents reference,
  pipeline-at-a-glance, routing table) and `constitution.md` (agent→section
  table). Backlog/B-NNN/add-to-backlog routing rows added.
- **`docs/constitution.md` brought up to v1.10.0:** §11.1/§11.2 split, §12
  Backlog discipline, §13 Release & versioning, and the `CONSTITUTION.project.md`
  / `§P` project-extension model now documented; the agent→section table and
  artifact maps updated.
- **`docs/customizing.md` "Adding constitution sections" rewritten** to direct
  project invariants into `CONSTITUTION.project.md` as `§P` sections.
- **Drift prevention (process):** `CLAUDE.project.md`'s version-bump rule gains a
  docs-sync check (a table mapping each kind of scaffold change to the `docs/`
  facts that mirror it), and `docs/audit-prompt.md` dimension 5 gains an explicit
  doc-drift sweep with counts.

### 1.11.0 — Forge-owned file changes (auto-applied by `/forge-update`)

- None. No changes to `.claude/agents/`, `.claude/commands/`, or
  `.claude/templates/`. `/forge-update` has nothing to auto-apply for this
  version.

### 1.11.0 — Non-forge-owned changes (manual review)

- `docs/*.md` — the operations manual. `docs/` is **not** auto-propagated by
  `/forge-update`; it lives in the forge repo. Projects that keep a verbatim
  copy of the manual can pull these updates by hand if they want them.
- `CLAUDE.project.md` (agent-forge-internal) — meta-work governance for the
  scaffold itself; not relevant to downstream projects.

### 1.11.0 — Manual steps for existing `CONSTITUTION.md`

None. This release is documentation and process only — no `CONSTITUTION.md`
changes are required.

### 1.11.0 — Verify

- [ ] Check `.forge-version` — should read `1.11.0`.
- [ ] `docs/task-flows.md` exists and renders its Mermaid diagrams.
- [ ] `grep -rn "16 agent\|Sixteen" docs/` returns no matches (count is 17).
- [ ] `docs/README.md` reading order lists 8 files including `task-flows.md`.

---

## 1.9.0 → 1.10.0 (2026-06-01)

### 1.10.0 — What changed

Resolves a structural collision waiting to happen: as forge grew numerically (§12 in v1.8.0, §13 in v1.9.0), it would eventually collide with projects that had added their own §14, §15, … to `CONSTITUTION.md`. The fix mirrors the established `CLAUDE.md` / `CLAUDE.project.md` pattern — split into a forge-owned base file and a project-owned extension file, with permanently disambiguated section numbering.

- **New CONSTITUTION §11.2 documents the project-extension convention.** The forge file (`CONSTITUTION.md`) owns numerical sections §1–§13 (and future numerical additions). Project-specific invariants live in a separate `CONSTITUTION.project.md` at the repo root, using `§P1`, `§P2`, `§P3`, … numbering. The `P` prefix is permanent — projects never use bare numbers, forge never uses `§P*`. No future collision is possible.
- **Project sections are additive only.** They may add or strengthen rules but may NOT contradict forge sections §1–§13. A contradicting project section is a `qa-reviewer` blocker — fix via §11.1 amendment or remove the contradicting rule.
- **Every agent that reads `/CONSTITUTION.md` MUST also read `/CONSTITUTION.project.md` if it exists.** The CLAUDE.md "Constitution" section now documents this dual-file reading rule explicitly. Agents that already cite the constitution inherit the rule transitively — they don't each need an inline edit.
- **`init-project` creates `CONSTITUTION.project.md`** as a new Step 11, between `CLAUDE.project.md` (Step 10) and `CONTRIBUTING.md` (Step 12). The stub has the convention documented inline and an example commented out for reference.
- **`forge-update`'s "will never touch" list** explicitly names `CONSTITUTION.project.md` — same protection as `CONSTITUTION.md`.

### 1.10.0 — Forge-owned file changes (auto-applied by `/forge-update`)

- `.claude/commands/init-project.md` — new Step 11 creates `CONSTITUTION.project.md`; subsequent steps renumbered 12 → 17
- `.claude/commands/forge-update.md` — `CONSTITUTION.project.md` added to "will never touch" list

### 1.10.0 — Non-forge-owned changes (manual review)

- `CLAUDE.md` — new "Dual-file reading rule" subsection in the Constitution section. Projects using `CLAUDE.md` mostly verbatim from the forge should pull this addition.
- `CONSTITUTION.template.md` — §11 split into §11.1 (existing amendment process) and §11.2 (project extensions). See migration steps below.

### 1.10.0 — Manual steps for existing `CONSTITUTION.md`

If your project's `CONSTITUTION.md` has sections numbered §14, §15, … (or any number above §13), they need to move to a new `CONSTITUTION.project.md` with `§P` renumbering. See [`docs/migrations/v1.10.0-constitution-project-file.md`](docs/migrations/v1.10.0-constitution-project-file.md) for step-by-step instructions including the cross-reference search.

If your project has NO sections beyond §13, this migration is still recommended — create an empty `CONSTITUTION.project.md` so future project rules have a defined home and don't sprawl back into the forge-owned file.

### 1.10.0 — Verify

- [ ] Check `.forge-version` — should read `1.10.0`.
- [ ] `CONSTITUTION.md` contains only forge-owned §1–§13 (plus Revision log).
- [ ] `CONSTITUTION.project.md` exists at the repo root with the convention header.
- [ ] If you had project-specific sections: they now live in `CONSTITUTION.project.md` as §P1, §P2, … and `grep -rn "§14\|§15" .` returns no matches outside intentional migration-guide references.
- [ ] A reviewer agent run on code that would violate a project rule cites the `§P<N>` reference (not just §14 from old numbering).

---

## 1.8.0 → 1.9.0 (2026-06-01)

### 1.9.0 — What changed

Release & versioning becomes a first-class concern parallel to backlog discipline (added in v1.8.0). Previously the forge had no opinion on how downstream projects should version themselves; each team invented an ad-hoc scheme or none at all. v1.9.0 adds a deliberate decision point at `/init-project` plus the agents that act on it.

- **New CONSTITUTION §13 "Release & versioning"** declares the project's scheme. Four options: `semver` (libraries, SDKs, CLIs), `calver` (apps, services, internal tools), `none` (continuous-deployment services), or `custom`. The scheme determines what each version-component means, the version field location, the changelog discipline, and the release process.
- **`/init-project` now asks a versioning question** (new Step 15) and fills §13 based on the answer, including the per-scheme description block. If the chosen scheme is anything other than `none`, init creates `CHANGELOG.md` at the repo root in Keep-a-Changelog format with an empty `## [Unreleased]` section and the six standard categories.
- **`release-engineer` Gate 1 extended.** Before opening the PR, it reads §13.1 and applies the chosen scheme: bumps the version field at the declared manifest path, renames `## [Unreleased]` to `## [<new-version>] — <today>` in CHANGELOG.md, opens a fresh `Unreleased` above, and creates the git tag on merge. If §13.1 is missing or `version field location` is `_TBD_`, it CLARIFY-blocks rather than guessing. If the scheme is `none`, it skips all version operations.
- **`doc-writer` now maintains `CHANGELOG.md` `Unreleased`.** Every feature it documents also gets a one-bullet entry under the appropriate category. Skipped if scheme is `none`.
- **`forge-update` "will never touch" list** extended with `CHANGELOG.md` (project-owned, just like `BACKLOG.md`).
- **`CLAUDE.md` output-artifact map** gains the `/CHANGELOG.md` row.

### 1.9.0 — Forge-owned file changes (auto-applied by `/forge-update`)

- `.claude/commands/init-project.md` — new Step 15 (versioning question + conditional CHANGELOG.md creation); subsequent steps renumbered
- `.claude/agents/release-engineer.md` — constitution-precedence bullet extended to include §13; new Gate 1 operating rule for version bump + CHANGELOG rotation
- `.claude/agents/doc-writer.md` — constitution-precedence bullet extended to include §13; new operating rule for CHANGELOG.md `Unreleased` maintenance
- `.claude/commands/forge-update.md` — `CHANGELOG.md` added to "will never touch" list

### 1.9.0 — Non-forge-owned changes (manual review)

- `CLAUDE.md` — output-artifact map adds `/CHANGELOG.md`. Projects using `CLAUDE.md` verbatim should pull this.
- `CONSTITUTION.template.md` — new §13. See migration steps below.

### 1.9.0 — Manual steps for existing `CONSTITUTION.md`

Add §13 to your `CONSTITUTION.md` between §12 and the Revision log. See [`docs/migrations/v1.9.0-versioning.md`](docs/migrations/v1.9.0-versioning.md) for the exact content per scheme and step-by-step setup.

If you've already been versioning informally (e.g. occasional git tags), you can backfill `CHANGELOG.md` from existing tags — see Step 4 in the migration guide.

If you'd rather not adopt versioning at all, choose `none` in §13.1; `release-engineer` and `doc-writer` will skip all version operations cleanly.

### 1.9.0 — Verify

- [ ] Check `.forge-version` — should read `1.9.0`.
- [ ] `CONSTITUTION.md` has §13 with §13.1 `Scheme` set to a real value (not `_TBD_`).
- [ ] If scheme ≠ `none`: `CHANGELOG.md` exists at the repo root.
- [ ] Run any feature through `/autopilot` — `doc-writer` appends one bullet to `## [Unreleased]` in CHANGELOG.md (or skips silently if scheme is `none`).
- [ ] On release: `release-engineer` renames `Unreleased` to a dated version section, opens a fresh `Unreleased` above, and the merge produces a git tag `v<new-version>` (or skips if `none`).

---

## 1.7.0 → 1.8.0 (2026-06-01)

### 1.8.0 — What changed

Backlog discipline as a first-class concern across the forge. Previously, minor review findings landed in their respective reports (`/docs/qa-reports/`, `/docs/code-reviews/`, etc.) and were silently forgotten. Three named consequences drove this release:

1. **Tech debt was invisible.** No aggregated view of deferred work across the project.
2. **Patterns were lost across sessions.** A reviewer seeing a singleton "nice-to-have" couldn't know that two previous reviewers had seen the same thing in different files — so it never reached the threshold where it became a real concern.
3. **`fix-now` was unenforced.** Reviewers could file an arbitrary number of minor findings and the pipeline would converge without addressing any of them.

Solution:

- **New CONSTITUTION §12 "Backlog discipline"** binds severity to action: `blocker` fixed inline, `major` fixed inline or deferred with reason, `minor` always logged to `BACKLOG.md`. Reviewer-internal names (`nit`, `nice-to-have`, `LOW`) all collapse to canonical `minor`. ALL minor findings go to backlog — singletons included — because pattern detection across sessions requires them to be recorded.
- **New `BACKLOG.md` at the repo root.** Created by `/init-project`; appended by review agents during convergence; closed by `refactor-specialist` when an entry's fix lands. Project-owned (never touched by `/forge-update`).
- **New `backlog-curator` agent.** Read-only grooming. Detects cross-session patterns (`Type` + `Suggested fix` keyword clusters), proposes minor→major consolidation when ≥3 active entries describe the same pattern, flags stale singletons (>180 days) for archival, surfaces systemic warnings when one `Type` exceeds 30% of active entries. Produces a proposal report at `/docs/backlog-reviews/<YYYY-MM-DD>.md`; user approves; `refactor-specialist` or orchestrator applies.
- **`refactor-specialist` now accepts a `B-NNN` backlog ID as input.** Reads the entry, executes the refactor, moves the entry to "Closed entries" with a `Resolved:` annotation.
- **`autopilot` Phase 0 (NEW) — backlog pre-flight.** Before opening intake, scans `BACKLOG.md` for past-deadline entries and offers the user a chance to groom first. Non-blocking; default is "continue with the feature."
- **`autopilot` Phase 3 — atomic backlog write.** After parallel reviewers complete, the orchestrator extracts every minor finding from their reports and writes them to `BACKLOG.md` in one atomic step before checking convergence.
- **Six review agents updated** (`qa-reviewer`, `code-reviewer`, `security-auditor`, `performance-analyst`, `ux-consultant`, `observability-auditor`) to encode the new rule: minor findings go to BACKLOG.md, not inline. Convergence no longer blocks on minor.
- **`init-project` creates `BACKLOG.md`** (new Step 12; subsequent steps renumbered).
- **`CLAUDE.project.md` extends backlog discipline to agent-forge meta-work** — the same rule applies to scaffold changes. No more "I'll get to it" promises in chat.

### 1.8.0 — Forge-owned file changes (auto-applied by `/forge-update`)

- `.claude/agents/backlog-curator.md` — NEW agent (read-only grooming, pattern detection, proposals)
- `.claude/agents/qa-reviewer.md` — operating rules: minor → BACKLOG.md, convergence closes on zero blocker/major
- `.claude/agents/code-reviewer.md` — nit → BACKLOG.md (all instances including singletons); forbidden action updated
- `.claude/agents/security-auditor.md` — LOW → BACKLOG.md; no downgrade-to-avoid-inline
- `.claude/agents/performance-analyst.md` — minor → BACKLOG.md
- `.claude/agents/ux-consultant.md` — nice-to-have → BACKLOG.md (all instances); forbidden action updated
- `.claude/agents/observability-auditor.md` — minor → BACKLOG.md
- `.claude/agents/refactor-specialist.md` — accepts `B-NNN` backlog ID input; closes entry on completion
- `.claude/commands/autopilot.md` — Phase 0 backlog pre-flight added; Phase 3 atomic BACKLOG write added; loop body renumbered
- `.claude/commands/init-project.md` — new Step 12 creates `BACKLOG.md`; subsequent steps renumbered
- `.claude/commands/forge-update.md` — `BACKLOG.md` added to "will never touch" list

### 1.8.0 — Non-forge-owned changes (manual review)

- `CLAUDE.md` — routing table extended with backlog operations; specialist list adds `backlog-curator`; output-artifact map adds `/docs/backlog-reviews/` and `/BACKLOG.md`. Projects using `CLAUDE.md` verbatim from the forge should pull these changes.
- `CLAUDE.project.md` — meta-work discipline extended. Bootstrapped projects have only the placeholder template; this addition does not apply downstream.
- `CONSTITUTION.template.md` — new §12 "Backlog discipline". See migration steps below.

### 1.8.0 — Manual steps for existing `CONSTITUTION.md`

Add a new §12 "Backlog discipline" before the Revision log section. See `docs/migrations/v1.8.0-backlog-discipline.md` for the exact content to paste. Then:

1. Create `BACKLOG.md` at your project root. Copy the content from the new `init-project.md` Step 12 (substituting your product name).
2. The new severity model takes effect on the next pipeline run. Findings already in your existing `/docs/qa-reports/` minors are NOT auto-migrated — if you want them tracked, copy them into `BACKLOG.md` manually now.

### 1.8.0 — Verify

- [ ] Check `.forge-version` — should read `1.8.0`.
- [ ] `BACKLOG.md` exists at the repo root with "Active entries" and "Closed entries" sections.
- [ ] `.claude/agents/backlog-curator.md` exists.
- [ ] Run any reviewer on a piece of code with a known minor issue — the report describes it as minor, and (in autopilot) the orchestrator writes a B-NNN entry to BACKLOG.md.
- [ ] Invoke `backlog-curator` against a backlog with ≥3 similar entries — output report proposes a consolidation.
- [ ] Invoke `refactor-specialist B-001` against an active entry — agent reads, executes, closes the entry.

---

## 1.6.0 → 1.7.0 (2026-06-01)

### 1.7.0 — What changed

Final pass of audit cleanup plus a documented semver model so future bumps stay disciplined.

- **`init-project` now asks a fourth test strategy question: coverage floor.** Options: no floor (tracked but not gated) / 50% / 70% / 80%. Fills CONSTITUTION §4 `Coverage floor` (previously left `_TBD_` forever). This is the only MINOR-worthy change in this release; everything else is hardening or cleanup.
- **`requirements-intake` hard-blocks on §1 `TBD`.** Previously a soft rule ("ask if the request implies a stack"); now an unconditional `URGENT: yes` CLARIFY before any other questions are drafted, regardless of request shape. The README/CLAUDE.md "intake refuses to lock a ticket while §1 stays TBD" promise is now enforced in the agent itself.
- **`autopilot.md` documents multi-day Phase 3 report resolution.** When convergence runs across calendar days, multiple dated reports may exist for the same artifact type; the orchestrator now MUST pass the most-recent-by-mtime file to `release-engineer`.
- **`release-engineer` Operating rules now carry Gate labels.** Every rule is tagged `(Gate 1)` through `(Gate 5)`, or `(Gate 3 prerequisite)` / `(Cross-cutting)` / `(Post-gates)` where it doesn't map 1:1 to one gate. Cosmetic readability, no behavior change.
- **`ux-consultant` gains a "no nice-to-have-only review" rule.** Parallel to `code-reviewer`'s no-nits-only rule. Pure nice-to-have findings get a chat summary instead of a filed report.
- **`CLAUDE.project.md` documents the semver model.** MAJOR for breaking changes, MINOR for new capability, PATCH for fixes and cleanup. Past bumps drifted toward MINOR-everything; the model exists to prevent recurrence.

### 1.7.0 — Forge-owned file changes (auto-applied by `/forge-update`)

- `.claude/commands/init-project.md` — new "Question D" (coverage floor) added to the test strategy step; corresponding §4 update rule added
- `.claude/commands/autopilot.md` — multi-day date-resolution rule added to Phase 4a invocation
- `.claude/agents/requirements-intake.md` — Mode A step 1 split into hard `§1 TBD` block + soft `other TBD` note; operating-rules "Refuse to invent stack decisions" tightened to match
- `.claude/agents/release-engineer.md` — Operating rules now carry Gate labels (`(Gate N)` / `(Gate N prerequisite)` / `(Cross-cutting)` / `(Post-gates)`)
- `.claude/agents/ux-consultant.md` — new forbidden action: no nice-to-have-only reviews

### 1.7.0 — Non-forge-owned changes (manual review)

- `CLAUDE.project.md` — semver model documented; applies to anyone working on agent-forge itself. Bootstrapped projects that pulled `CLAUDE.project.md` from `init-project` have only the placeholder template; this addition does not apply downstream.

### 1.7.0 — Manual steps for existing `CONSTITUTION.md`

None for downstream projects.

**Optional:** If your project's `CONSTITUTION.md` §4 still has `Coverage floor: _TBD_ %`, decide a value now (`0` for "track but don't gate", or `50` / `70` / `80`) and fill it in — `spec-architect` §10.1 references it for every spec.

### 1.7.0 — Verify

- [ ] Check `.forge-version` — should read `1.7.0`.
- [ ] Run `/init-project` on a fresh clone — the test strategy step asks **four** questions (isolation, cloud policy, E2E scope, coverage floor) instead of three.
- [ ] Open `.claude/agents/requirements-intake.md` — Mode A step 1 has the "Hard pre-condition: §1 must not be TBD" bullet.
- [ ] Open `.claude/agents/release-engineer.md` Operating rules — bullets carry `(Gate N)` labels.
- [ ] Open `.claude/agents/ux-consultant.md` Forbidden actions — "File a review whose findings are all `nice-to-have`" rule is present.

---

## 1.5.0 → 1.6.0 (2026-06-01)

### 1.6.0 — What changed

Audit pass after three rapid version bumps (v1.3.0–v1.5.0). Resolves the structural inconsistencies and documentation drift the audit surfaced. No new features.

- **`release-engineer` reverts to five gates.** v1.2.0 had added a sixth "local hygiene" gate that contradicted the agent's own "never merge the PR" forbidden action — the gate could not complete on the default flow because it expected a merged PR. The closing line (delete the local branch after merge) is now a human-facing reminder in the release report, not a blocking gate. Aligns with `autopilot.md`, `CLAUDE.md`, and `CONSTITUTION.template.md`, all of which already documented five gates.
- **`CLAUDE.md` routing table disambiguated.** The bare token `"deploy"` previously matched both `devops-engineer` (authoring the deploy pipeline) and `release-engineer` (executing the deploy). Now: `devops-engineer` matches `"deploy pipeline"`, `release-engineer` matches `"deploy this"`. The phrase `"clean this up"` moves from `code-reviewer` (read-only) to `refactor-specialist` (which actually performs the cleanup). `code-reviewer` keeps `"looks good?"`.
- **`developer` forbidden actions tightened.** Two new bullets enforce pipeline ordering at the manual-mode boundary: cannot write code without `/docs/specs/<feature>.md`; cannot touch data-layer code when the spec references a data model that has no migration. Previously these were only implicit in the mission statement.
- **`spec-architect` SDD §10.1 wording fix.** The CI-gate row was labelled `"CI gate"` but inherited from CONSTITUTION §4.3 which is titled `"E2E policy"`. Row label now matches the constitution section title. Coverage-target wording handles the `_TBD_` case explicitly.
- **`CLAUDE.md` code-reviewer description corrected.** Previously said `"runs between developer and qa-reviewer"`; autopilot actually runs them in parallel during Phase 3 convergence.
- **`README.md` rewritten.** No longer duplicates the bootstrap checklist (which had drifted four steps behind `CLAUDE.md`'s authoritative version). README now points at `CLAUDE.md` for the canonical bootstrap procedure and summarises only the high-level pipeline shape.
- **`docs/migrations/v1.2.0-accessibility-section.md` created.** This file was referenced from `UPGRADING.md` v1.1.0 → v1.2.0 but did not exist. Pre-v1.2.0 projects can now actually complete the §7 migration.
- **`UPGRADING.md` v1.3.0 entry de-numbered.** Verify checklist referenced "Step 10" which had shifted to Step 13 after v1.5.0; references now use step names rather than numbers to survive future renumbering.

### 1.6.0 — Forge-owned file changes (auto-applied by `/forge-update`)

- `.claude/agents/release-engineer.md` — mission reverts to "five things"; Gate 6 operating rule replaced with informational closing-line rule; forbidden actions updated to remove the Gate 6 reference
- `.claude/agents/spec-architect.md` — §10.1 row labels aligned with CONSTITUTION §4 subsection titles
- `.claude/agents/developer.md` — two forbidden-actions bullets added (no code without spec; no data layer without database-designer)
- `.claude/commands/forge-update.md` — no change in this version (previous v1.5.0 update covers the project-owned list)

### 1.6.0 — Non-forge-owned changes (manual review)

These changed in this version but aren't auto-applied (they're project-owned or repo-root):

- `CLAUDE.md` — routing table disambiguation and code-reviewer description fix. Projects using `CLAUDE.md` mostly verbatim from the forge will want to apply these manually.
- `README.md` — rewritten in the forge repo; bootstrapped projects already have a stub README from `/init-project`, so no action.
- `UPGRADING.md` — added this v1.6.0 entry; the v1.3.0 entry's stale step references were rewritten.
- `docs/migrations/v1.2.0-accessibility-section.md` — new file; ships via `docs/migrations/` which `/forge-update` preserves but does not actively copy. Users upgrading from <v1.2.0 should pull this file by hand.

### 1.6.0 — Manual steps for existing `CONSTITUTION.md`

None.

**Optional sanity check:** if your project's `CLAUDE.md` was customised from the forge's, scan its routing table for the bare `"deploy"` token and decide whether you want the disambiguation applied locally.

### 1.6.0 — Verify

- [ ] Check `.forge-version` — should read `1.6.0`.
- [ ] Open `.claude/agents/release-engineer.md` — mission says "verify five things, in order"; no Gate 6.
- [ ] Open `CLAUDE.md` — routing table no longer has bare "deploy" in two rows; `code-reviewer` description says "runs in parallel with qa-reviewer".
- [ ] Open `.claude/agents/developer.md` — Forbidden actions list includes "Write code when `/docs/specs/<feature>.md` does not exist".
- [ ] Open `docs/migrations/v1.2.0-accessibility-section.md` — file exists.

---

## 1.4.0 → 1.5.0 (2026-06-01)

### 1.5.0 — What changed

- **`/init-project` now cleans up forge-internal documentation.** Bootstrapping a fresh template removes the agent-forge documentation files (`docs/audit-prompt.md`, `customizing.md`, `getting-started.md`, `how-it-works.md`, `intent.md`, `troubleshooting.md`, `constitution.md`, `README.md`) so the product project starts with a clean workspace. `docs/migrations/` is preserved because `/forge-update` needs it.
- **`/init-project` now writes a project stub `README.md`** pointing at `CONTRIBUTING.md`. Previously the forge's own README stayed at the root and was only replaced by `doc-writer` on the first feature ship — confusing in the meantime.
- **`/init-project` now creates `CONTRIBUTING.md`** — a short pointer document with the product name filled in, a brief pipeline overview, common workflows, where things live, and a link back to the agent-forge GitHub repo. `CONTRIBUTING.md` is project-owned; `/forge-update` never touches it.
- **`/forge-update` "will never touch" list** explicitly names `README.md` and `CONTRIBUTING.md` as project-owned.

### 1.5.0 — Forge-owned file changes (auto-applied by `/forge-update`)

- `.claude/commands/init-project.md` — three new steps (cleanup, README stub, CONTRIBUTING.md); renumbered following steps; forbidden actions updated to forbid deleting `docs/migrations/` and no longer forbid modifying `README.md`
- `.claude/commands/forge-update.md` — "will never touch" list extended with `README.md` and `CONTRIBUTING.md`

### 1.5.0 — Manual steps for existing `CONSTITUTION.md`

None.

**Optional cleanup for projects bootstrapped before v1.5.0:** the forge-internal docs are still in your `docs/` directory. You can safely delete them manually (they were never used by your project):

```sh
rm docs/README.md docs/audit-prompt.md docs/constitution.md docs/customizing.md docs/getting-started.md docs/how-it-works.md docs/intent.md docs/troubleshooting.md
```

Keep `docs/migrations/`.

**Optional: create `CONTRIBUTING.md`.** Open `.claude/commands/init-project.md` after running `/forge-update`, copy the CONTRIBUTING.md content from Step 11, replace `<product-name>` with your project name, and save to `CONTRIBUTING.md` at the repo root.

**Optional: shrink `README.md` to a stub.** Replace your root `README.md` with the stub content from `init-project.md` Step 7 if you'd prefer that `doc-writer` builds the product README from scratch on a future feature ship.

### 1.5.0 — Verify

- [ ] Check `.forge-version` — should read `1.5.0`.
- [ ] Run `/init-project test-product` on a fresh clone — `docs/` should contain only `migrations/` after init; root should have `CONTRIBUTING.md` and a stub `README.md`.
- [ ] Open the generated `CONTRIBUTING.md` — should have the product name filled in and link to <https://github.com/pthode/agent-forge>.

---

## 1.3.0 → 1.4.0 (2026-06-01)

### 1.4.0 — What changed

- **`UPGRADING.md` now documents per-version file changes.** Each version entry lists the exact forge-owned files that changed. `/forge-update` uses this list to scope its diff to only the relevant files, rather than scanning all forge-owned files on every run.
- **`CLAUDE.project.md`** gains a mandatory anti-pattern: any commit touching scaffold files must be accompanied by a bumped `.forge-version` and a new `UPGRADING.md` entry.

### 1.4.0 — Forge-owned file changes (auto-applied by `/forge-update`)

- `.claude/commands/forge-update.md` — Step 3 updated to use UPGRADING.md "Forge-owned file changes" lists to scope the diff; falls back to full scan if UPGRADING.md is absent or doesn't cover the version range
- `CLAUDE.project.md` — anti-pattern added: always bump `.forge-version` and add an UPGRADING.md entry when committing scaffold changes

### 1.4.0 — Manual steps for existing `CONSTITUTION.md`

None.

### 1.4.0 — Verify

- [ ] Check `.forge-version` — should read `1.4.0`.
- [ ] Run `/forge-update` — output should mention "Checking N files from changelog" rather than scanning all forge-owned files.

---

## 1.2.0 → 1.3.0 (2026-06-01)

### 1.3.0 — What changed

- **Test strategy captured during `/init-project`.** Three questions (local isolation strategy, cloud dev policy, E2E scope) fill `CONSTITUTION.md` §4.1–4.3 at bootstrap. `test-engineer` pre-conditions on §4.1 being set before writing any test. `spec-architect` SDD template gains §10.1 "Test execution requirements" for feature-level exceptions.
- **CONSTITUTION template §4** gains three sub-sections: §4.1 Test environment contract, §4.2 TDD policy, §4.3 E2E policy — each with a `[scope: TBD]` marker that `/init-project` fills in.

### 1.3.0 — Forge-owned file changes (auto-applied by `/forge-update`)

- `.claude/agents/test-engineer.md` — pre-condition added: checks for "Test environment contract" subsection in CONSTITUTION.md before writing tests; emits CLARIFY BLOCKED:yes if absent or `[scope: TBD]`
- `.claude/agents/spec-architect.md` — §10.1 "Test execution requirements" added to SDD template
- `.claude/commands/init-project.md` — a new "Ask the test strategy questions" step inserted before "Print the next-step checklist"; checklist gains an item to review §4.1 (specific step numbers in init-project.md may have shifted in later versions — refer to the file directly)

### 1.3.0 — Manual steps for existing `CONSTITUTION.md`

Your project's `CONSTITUTION.md` is not touched automatically. Add the following three sub-sections at the end of your test discipline section (§4 in standard constitutions, or whichever section contains "Test discipline"):

```markdown
### 4.1 Test environment contract
- **Local isolation strategy:** <none / in-memory substitutes / docker-compose / ci-only>
- **Services required for tests:** <N/A or list each service and its local equivalent>
- **Cloud dev policy:** <no-cloud / test-accounts / unrestricted>

[scope: set]

### 4.2 TDD policy
- spec-derived-post-impl — test-engineer after developer, tests derived from spec (pipeline default)

[scope: set]

### 4.3 E2E policy
- <disabled / smoke-only / critical-paths / full>

[scope: set]
```

Fill in the `<placeholders>` to match what your project actually does. Use `[scope: set]` (not `TBD`) since you are filling them in directly. To have Claude Code fill them from evidence, open the project and say: _"Read the existing tests and CI config, then fill in CONSTITUTION.md §4.1, §4.2, and §4.3 to match what the project actually does."_

### 1.3.0 — Verify

- [ ] Check `.forge-version` — should read `1.3.0`.
- [ ] Open `CONSTITUTION.md` — should have §4.1, §4.2, §4.3 with `[scope: set]` markers.
- [ ] Invoke `test-engineer` — if §4.1 is missing or `[scope: TBD]`, it should emit a CLARIFY BLOCKED:yes.
- [ ] Run a `spec-architect` session — SDD output should include §10.1 "Test execution requirements".
- [ ] Run `/init-project` on a fresh clone — the test strategy step should ask three questions (local isolation, cloud dev policy, E2E scope) before printing the final checklist.

---

## 1.1.0 → 1.2.0 (2026-05-28)

### 1.2.0 — What changed

- **Accessibility section in CONSTITUTION template.** §7 "Accessibility & UX baseline" replaced the five-bullet stub with a structured §7.1–7.7 covering: guiding principle ("build from the edge in"), conformance standard with `<wcag_level>` placeholder, scope placeholder `<ui_surfaces>`, automated gate (stack-matched axe-core adapter, zero-violations CI hard gate), mandatory `ux-consultant` manual review, five baseline UX requirements, three-step third-party escalation policy, and a minimum AT matrix (NVDA/Firefox, VoiceOver/Safari, TalkBack/Chrome).
- **`requirements-intake`** gains a mandatory accessibility standard question (step 4, new) for features with UI surfaces. Fires when `<wcag_level>` is unfilled and the request involves any frontend surface. The `★ Q1` question (WCAG AA / AAA / project-specific) appears first in the batch because the answer affects component library choice, form patterns, and CI gate configuration. The question is skipped if §7.1 is already locked.

### 1.2.0 — Forge-owned file changes (auto-applied by `/forge-update`)

- `.claude/agents/requirements-intake.md` — step 4 (accessibility standard question) inserted; prior step 4 renumbered to step 5; prior step 5 renumbered to step 6; "accessibility standard (UI features only)" bullet added to gap-identification dimension list

### 1.2.0 — Manual steps for existing `CONSTITUTION.md`

Your project's `CONSTITUTION.md` is not touched automatically. Apply the §7 restructuring manually.

See [docs/migrations/v1.2.0-accessibility-section.md](docs/migrations/v1.2.0-accessibility-section.md) for the exact replacement content.

Summary of what to do:

1. Find your current accessibility section (the five-bullet stub, likely titled "Accessibility & UX baseline (frontend only)").
2. Replace it entirely with the §7.1–7.7 structure from the migration guide.
3. Fill in `<wcag_level>` with your project's target (`AA` is the default).
4. Fill in `<ui_surfaces>` with the list of surfaces this project exposes.
5. Trim the TalkBack row from §7.7 if your project has no mobile-web surface.

### 1.2.0 — Verify

- [ ] Check `.forge-version` — should read `1.2.0`.
- [ ] Run a UI feature through `/autopilot` — `requirements-intake` should emit the `★ Q1` accessibility question before any other gap question.
- [ ] After answering (a) or (b), confirm the locked ticket records the `wcag_level` value.
- [ ] Check that `ux-consultant` is still listed as mandatory in your pipeline's convergence reviewers.
- [ ] Inspect your `CONSTITUTION.md` §7 — should have §7.1–7.7 subsections, not the five-bullet stub.

---

## 1.0.0 → 1.1.0 (2026-05-27)

### 1.1.0 — What changed

- **Monitoring taxonomy in CONSTITUTION template.** §8 "Observability & event logging" restructured into four sub-sections (§8a–d) covering operational observability, audit logging, product analytics, and security event monitoring. Each sub-section has a `[scope: disabled | enabled | always-on]` marker so agents know which concerns are active.
- **`observability-auditor`** extended with Step 0: reads §8 sub-section scope markers and builds audit scope from them. Disabled concerns are skipped. Missing spec §10 for an enabled concern is filed as a **major** finding.
- **`spec-architect` SDD template** gains §10 "Observability plan" — one table per enabled monitoring concern. Gives developer and devops-engineer a shared event contract per feature instead of inferring from §7.
- **`developer`** must now implement spec §10 rows in full (enum/const event names, correct level, required fields). Undocumented events require a CLARIFY to spec-architect.
- **`requirements-intake`** asks a monitoring scope question when any of §8b/§8c/§8d is `scope: enabled` — surfaces feature-specific monitoring scope before the spec is written.
- **`init-project`** now asks three yes/no questions during bootstrap (audit logging? product analytics? security monitoring?) and flips the corresponding §8 scope markers.
- **Upgrade process (this file + `/forge-update` command)**. Projects built on forge can now receive scaffold updates without manually tracking git commits.
- **`.forge-version` file**. Tracks which forge version a project was built from or last updated to.

### 1.1.0 — Forge-owned file changes (auto-applied by `/forge-update`)

- `.claude/agents/observability-auditor.md` — Step 0 (scope-aware audit) prepended to Operating rules; spec §10 is now the primary event contract source
- `.claude/agents/spec-architect.md` — §10 Observability plan with four concern tables added to SDD template
- `.claude/agents/developer.md` — §10 implementation obligation added to Operating rules
- `.claude/agents/requirements-intake.md` — monitoring scope question added to Mode A gap-identification list
- `.claude/commands/init-project.md` — step 7 (monitoring scope questions) added; step 8 next-steps checklist updated

### 1.1.0 — Manual steps for existing `CONSTITUTION.md`

Your project's `CONSTITUTION.md` is not touched automatically. Apply the §8 restructuring manually.

See [docs/migrations/v1.1.0-monitoring-taxonomy.md](docs/migrations/v1.1.0-monitoring-taxonomy.md) for the exact content to insert.

Summary of what to do:
1. Find your current §8 / Observability section (the bullet-list version).
2. Replace it with the four sub-section structure from the migration guide.
3. Choose scope markers: §8a is always `always-on`; decide `enabled` vs `disabled` for §8b (audit), §8c (analytics), §8d (security monitoring) based on your project's needs.
4. Fill in TBD platform fields for any section you enable.

### 1.1.0 — Verify

- [ ] Run a `spec-architect` session for any feature — SDD output should include §10 with at least an §8a table.
- [ ] Run `observability-auditor` — Step 0 should appear at the top of its operating-rules section.
- [ ] Check `.forge-version` — should read `1.1.0`.
- [ ] If §8b or §8d is enabled in your CONSTITUTION: run a feature with an audit event — spec §10 should have an §8b table, and observability-auditor should verify it.
