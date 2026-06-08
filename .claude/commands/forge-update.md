---
name: forge-update
description: Update forge-owned scaffold files (.claude/agents/, .claude/commands/, .claude/templates/, CLAUDE.md) from an upstream agent-forge source. Shows a diff for review before applying. Never touches CONSTITUTION.md, CONSTITUTION.project.md, CLAUDE.project.md, src/, tests/, docs/ project artifacts, settings files, or memory.
---

# /forge-update — pull scaffold updates from upstream agent-forge

Brings forge-owned files in this project up to date with a newer version of agent-forge.
**Always runs as a plan-and-review operation: show the diff, confirm with the user, then apply.**

---

## What this command owns

**Will update (forge-owned):**
- `.claude/agents/*.md` — all agent definitions
- `.claude/commands/*.md` — all slash command definitions
- `.claude/templates/` — ticket template and other scaffolding inputs
- `CLAUDE.md` — the forge router playbook. Your project-specific additions live in `CLAUDE.project.md` (never touched), so this file is updated wholesale without losing them. This is the whole point of the `CLAUDE.md` / `CLAUDE.project.md` split.

**Will never touch (project-owned):**
- `CONSTITUTION.md` — your project's constitution; migrate manually using `UPGRADING.md`
- `CONSTITUTION.project.md` — project-owned constitution extensions (`§P1`, `§P2`, …); never touched by forge
- `CLAUDE.project.md` — your project's router additions (imported by `CLAUDE.md`); this is exactly what survives a `CLAUDE.md` update
- `README.md` — owned by the project (initially a stub from `/init-project`, expanded by `doc-writer`)
- `CONTRIBUTING.md` — project-owned workflow document created by `/init-project`; teams edit freely
- `BACKLOG.md` — project-owned tech-debt log (created by `/init-project`, written by reviewers and refactor-specialist)
- `CHANGELOG.md` — project-owned release notes (created by `/init-project` when versioning is enabled, written by doc-writer and release-engineer per CONSTITUTION §13)
- `src/`, `tests/`, `migrations/`, `infra/` — product code
- `docs/specs/`, `docs/requirements/`, `docs/qa-reports/`, etc. — pipeline artifacts
- `.claude/settings.json`, `.claude/settings.local.json` — permission model
- `.claude/memory/` — project memory

---

## Step 1 — Identify the forge source

Ask the user which source to compare against. Accept one of three options:

**Option A — git remote named `forge-upstream`**
The project has `forge-upstream` registered as a git remote pointing at agent-forge.

Setup (if not yet done):
```
git remote add forge-upstream <url-of-agent-forge-repo>
git fetch forge-upstream
```

Use this command to produce the diff:
```
git diff HEAD forge-upstream/main -- .claude/agents/ .claude/commands/ .claude/templates/ CLAUDE.md
```

**Option B — path to a local agent-forge clone**
The user points at a local directory (e.g. `z:\pt\agent-forge`).

Produce the diff by reading files from the source path and comparing against project files.
List any file that differs or is missing in the project.

**Option C — manual UPGRADING.md review**
No automated diff. Read `UPGRADING.md` (from the forge source if available, or the one
already in the project) and print the relevant entries between the project's current
`.forge-version` and the latest version. Guide the user through manual application.

---

## Step 2 — Read the current version

Read `.forge-version` in the project root.
- If the file exists: this is the current forge version (e.g. `1.0.0`).
- If it does not exist: version is unknown; warn the user and proceed with caution.

Read `.forge-version` in the forge source (option A or B).
- This is the target version.

Print: `Updating forge scaffold from v<current> to v<target>.`

---

## Step 2.5 — Self-update preflight (the command updates itself first)

`/forge-update` is itself a forge-owned file (`.claude/commands/forge-update.md`). The invocation you are running is the **project's current copy** — so if a newer agent-forge changed the update logic itself (a new preflight gate, a new safety step), that newer logic is NOT yet in effect for this run. Driving the whole apply with stale logic means a newer safety step never runs on the very update that installs it.

To close this bootstrapping gap, the command updates *itself* first.

**For option A or B:**

1. **Compare** the project's `.claude/commands/forge-update.md` against the source's.
   - Option A: `git diff --quiet HEAD forge-upstream/main -- .claude/commands/forge-update.md` (non-zero exit = differs).
   - Option B: diff the file read from the source path against the project's.
2. **Identical** → this run is already on the latest update logic. Continue to Step 3.
3. **Differs** → do a single-file self-update and stop:
   - Tell the user: "`forge-update` itself is out of date. I'll update only the command file first, then you re-run `/forge-update` so the current logic drives the actual update."
   - Ask for approval — this is a forge-owned write, so the Step 4 approval rule applies.
   - On approval, update **only** `.claude/commands/forge-update.md` (option A: `git checkout forge-upstream/main -- .claude/commands/forge-update.md`; option B: copy that one file from the source). Do **NOT** touch any other forge-owned file, and do **NOT** change `.forge-version` — the real update has not happened yet, so the version interval must stay intact for the re-run.
   - **Stop. Instruct the user to run `/forge-update` again.** The re-run finds an identical `forge-update.md`, passes this step, and proceeds through Steps 3–6 with the up-to-date logic (including any newer preflight / breaking-change gates).

**For option C** (manual UPGRADING.md walkthrough): there is no automated source to self-update from. Instead, read the **source's** `forge-update.md` (if available) or the latest `UPGRADING.md`, and follow *those* steps — not the project's current copy — so you are not walking through stale instructions.

This step is idempotent: once the command file matches the source, re-running `/forge-update` skips straight past it. (One unavoidable bootstrap remains: the jump that first *installs* a new Step 2.5 still runs on the old logic — every self-update mechanism has a version zero it cannot protect. All jumps after it are covered.)

---

## Step 3 — Show the diff (plan step — do not apply yet)

For option A or B:

**Scoped diff (preferred):** Read `UPGRADING.md` from the forge source. Find all version entries between the project's current `.forge-version` and the target version. For each entry, read the "Forge-owned file changes" list. Diff only those files. Print: `Checking N files from changelog (vX → vY).`

**Full scan (fallback):** If `UPGRADING.md` is absent in the source, or does not cover the full version range, fall back to scanning all forge-owned files. Print: `UPGRADING.md missing or incomplete — scanning all forge-owned files.`

For each file in scope:

1. List every file that differs between the project and the source.
2. For each changed file, show a human-readable summary: what sections were added/removed/changed.
   Do NOT dump the full file diff unless the user asks — keep the summary scannable.
3. List any forge-owned file that exists in the source but is missing from the project (new files).
4. List any forge-owned file that exists in the project but is missing from the source (deleted files — flag these, do not auto-delete).

For option C: print the UPGRADING.md entries between current and target version.

Do NOT ask for apply approval yet — the preflight gate (Step 3.5) runs first.

---

## Step 3.5 — Preflight: requirement & breaking-change gate (plan step — runs before apply approval)

Forge-owned files are overwritten wholesale, so a newer agent or command may
assume a project-owned prerequisite (a `CONSTITUTION.md` section, a settings
rule) that an earlier version introduced only as a **manual step** — and manual
steps are advisory, never enforced. This gate catches a missing prerequisite
**before** apply, regardless of which version the project is coming from, so the
mismatch surfaces here instead of as a runtime CLARIFY/blocker after the update.

### 3.5a — Requirement preflight (`Requires:` assertions)

For every version entry in the `[current, target]` interval, read its
**`Requires (preflight)`** list, if present. Each item is a self-contained
assertion of the form:

> `<project-file>` must contain `<pattern>` — `<why + remediation>`

Each assertion states what the forge code at that version needs to be true in
the project **right now** — it does NOT reference when the prerequisite was
introduced. This is what makes the check robust to a skipped manual step from
*any* prior version: the target version re-declares everything its code
depends on, so a project arriving from a version below the one that introduced
the prerequisite is still checked.

For each assertion, Grep the named project file for the pattern:

- **All assertions hold** → continue to 3.5b.
- **Any assertion fails** → **BLOCK. Do not apply.** Print, for each unmet
  requirement: the version that declared it, the file + pattern that is
  missing, the stated reason, and the remediation (usually "apply the
  `vX.Y.Z` manual steps first"). Tell the user the update is paused until the
  prerequisite is satisfied, then stop. Re-running `/forge-update` after the
  user fixes the prerequisite re-checks cleanly.

### 3.5b — Breaking-change boundary (`BREAKING` marker)

Scan the same interval for any entry carrying a **`⚠ BREAKING`** marker (a
version that crosses a MAJOR boundary per the semver model in
`CLAUDE.project.md`).

- **No breaking entry in range** → proceed to the apply confirmation below.
- **One or more breaking entries in range** → **hard-stop.** For each, print
  the version, a one-line summary of the break, and the
  `docs/migrations/v<x>.0.0-<name>.md` guide reference. Require the user to
  **explicitly confirm they have read each referenced migration guide** before
  apply proceeds. A plain "yes" to the diff is not sufficient — the
  confirmation must name the breaking version(s).

### 3.5c — Apply confirmation

Only once 3.5a passes and any 3.5b confirmation is given:

Ask the user: "Apply these changes? (yes / no / show full diff for <file>)"

---

## Step 4 — Apply (only after explicit approval)

For option A:

**Before overwriting `CLAUDE.md`, capture the project's `Product:` line.** It is the one
project-specific value living inside the otherwise-forge-owned `CLAUDE.md` (set by `/init-project`),
and the wholesale checkout below reverts it to the template placeholder. Read the current
`**Product:**` line from the project's `CLAUDE.md` and hold it.

```
git checkout forge-upstream/main -- .claude/agents/
git checkout forge-upstream/main -- .claude/commands/
git checkout forge-upstream/main -- .claude/templates/
git checkout forge-upstream/main -- CLAUDE.md
```
Then copy `.forge-version` from forge source into the project.

**After the checkout, restore the `Product:` line.** `CLAUDE.md` now carries the template
placeholder (`**Product:** _template — …_`). If the line you captured names a real product (not the
placeholder), replace that placeholder line with the captured line — a single-line Edit; `CLAUDE.md`
is at the repo root, outside the `.claude/` scaffold-lock, so the Edit tool is permitted.

`CLAUDE.md` is otherwise overwritten wholesale — that is intended. Project-specific router
instructions belong in `CLAUDE.project.md` (never touched); the `Product:` line is the **sole
exception**, because it lives in `CLAUDE.md` by design — it must be visible at the top of the router
playbook.

For option B:
Copy the changed forge-owned files from the source path into the project. **Preserve the
`**Product:**` line the same way** — capture it before, restore it after the `CLAUDE.md` copy. Update
`.forge-version` to match the source's version.

For option C: print instructions; the user applies manually — including a reminder to keep their
existing `**Product:**` line when they overwrite `CLAUDE.md`.

---

## Step 5 — Print manual migration steps

After applying forge-owned file updates, check `UPGRADING.md` for the versions covered
by this update. Print any **Manual steps** entries verbatim — these describe changes to
`CONSTITUTION.md` that require human judgment and are never auto-applied.

Say explicitly: "The following changes to CONSTITUTION.md are NOT automatic — apply them
manually when ready:" and list the migration guide references.

---

## Step 6 — Print the verify checklist

Print the **Verify** section from each UPGRADING.md entry that was applied.

Always include this standing check, regardless of version: **`CLAUDE.md`'s `**Product:**` line still
names the product, not the `_template` placeholder.** If it shows the placeholder, the Step 4 restore
was missed — fix it with a single-line edit.

---

## Forbidden actions

You MUST NOT:
- Apply any changes to forge-owned files without explicit user approval (step 3 must come before step 4).
- Drive the diff/apply (Steps 3–4) on a run where the project's `.claude/commands/forge-update.md` differs from the source. Self-update that one file first (Step 2.5), leave `.forge-version` unchanged, and re-run so the current update logic — not the project's stale copy — drives the actual upgrade.
- Apply when a Step 3.5a `Requires` assertion is unmet — block and print the unsatisfied prerequisite instead.
- Apply across a `⚠ BREAKING` boundary without the explicit, version-naming confirmation from Step 3.5b — a plain "yes" to the diff does not satisfy it.
- Touch `CONSTITUTION.md`, `CONSTITUTION.project.md`, `CLAUDE.project.md`, `src/`, `tests/`, `docs/` project artifacts, `.claude/settings.json`, `.claude/settings.local.json`, or `.claude/memory/`.
- Auto-delete forge-owned files that are missing from the source — flag them and let the user decide.
- Leave `CLAUDE.md`'s `**Product:**` line as the `_template` placeholder after an update — capture the project's line before the Step 4 overwrite and restore it after.
- Proceed if `.forge-version` in the project is HIGHER than in the source (downgrade) — stop and ask the user to confirm explicitly.
- Invent a forge source URL — only use what the user provides or what `git remote -v` shows for `forge-upstream`.
