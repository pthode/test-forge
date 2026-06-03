# Project-specific router instructions

This file extends `CLAUDE.md` with instructions specific to this project.
`CLAUDE.md` imports this file automatically at the end — Claude sees both.

For **agent-forge itself** (working on the scaffold), this file captures
meta-work rules that override the pipeline for scaffold development.

## Meta-work rules (agent-forge only)

When working on agent-forge itself — editing agents, commands, CLAUDE.md,
CONSTITUTION.template.md, or other scaffold files — the pipeline applies
to **product features** only. Meta-work on the scaffold uses direct edits
with in-conversation reasoning. Do NOT spin up pipeline subagents
(security-auditor, spec-architect, developer, etc.) when the change is
to the forge scaffolding itself.

## Workflow autonomy (agent-forge meta-work)

agent-forge has no `CONSTITUTION.md` (it is an un-bootstrapped template), so
its own autonomy level lives here rather than in CONSTITUTION §14.2. This is
the file the "Workflow autonomy" section of `CLAUDE.md` reads when
`CONSTITUTION.md` is absent.

- **Effective autonomy level for agent-forge meta-work: `autonomous`.** The
  owner's standing instruction is "merge og ryd op" — drive
  `commit → push → PR → merge` and branch cleanup without asking, within the
  §14.1 floor. This makes the standing instruction an explicit, versioned
  project setting instead of a hidden per-machine memory.
- **The floor still binds.** `main` stays PR-only and protected (push a
  branch, open a PR, squash-merge it — never push to `main` directly); the
  permission model is never loosened; CI must be green before merge; and
  security-sensitive changes (`.claude/settings.json`, CONSTITUTION §2/§5/§8,
  hooks, `Dockerfile`) always get explicit human confirmation. "Autonomous"
  is autonomy *within* the floor, not a bypass of it.
- **Still surface notable behavior changes** in the PR body so the owner can
  review after the fact, and **still ask** when a change is genuinely a
  design decision rather than execution (the autonomy is about the
  commit/merge mechanics, not about skipping design judgment).

## Project anti-patterns (agent-forge)

- **No framework on framework:** never invoke pipeline agents to modify
  the pipeline agents. Reason directly and edit scaffold files yourself.
- **One question at a time:** ask one focused question, never batch or
  bury multiple questions in one turn.
- **Backlog discipline applies to agent-forge itself.** When working on the
  scaffold, the same rule from CONSTITUTION §12 holds: minor findings about
  the scaffold (typos, doc-drift, low-priority refactors that don't justify
  a version bump on their own) MUST be appended to `BACKLOG.md` at the
  agent-forge repo root rather than left as informal "I'll get to it"
  promises in chat. Singletons are fine — `backlog-curator` finds the
  patterns across sessions. The seven minor findings we deferred from the
  v1.7.0 audit were exactly the kind of debt this rule prevents going
  forward.
- **Always bump version and changelog before committing scaffold changes.**
  Any edit to `.claude/agents/`, `.claude/commands/`, `.claude/templates/`,
  or `CONSTITUTION.template.md` MUST be accompanied in the same commit by:
  1. A bumped `.forge-version` per the **semver model below**.
  2. A new entry in `UPGRADING.md` for the bumped version, listing every changed
     forge-owned file under "Forge-owned file changes" and any required CONSTITUTION.md
     changes under "Manual steps". This is what `forge-update` uses to scope its diff.
     Never commit scaffold changes without these two files updated.
  3. A **docs-sync check** of the user-facing manual in `docs/`. The manual
     duplicates facts that live authoritatively elsewhere; when the source
     changes, the duplicate drifts. Before committing, verify each fact the
     change touches is consistent across its mirror in `docs/`:

     | If the change touches… | …re-check these docs facts |
     | --- | --- |
     | An agent's existence (add/remove) | agent count ("17 agents") in `README.md`, `how-it-works.md`, `intent.md`, `getting-started.md`, `audit-prompt.md`; agents reference + pipeline-at-a-glance + routing table in `how-it-works.md`; a flow in `task-flows.md` if it changes a handoff |
     | An agent's triggers / forbidden actions / outputs | that agent's entry in `how-it-works.md`; any `task-flows.md` flow it appears in |
     | The routing table in `CLAUDE.md` | the routing table in `how-it-works.md` |
     | An artifact path | the artifact maps in `CLAUDE.md` **and** `how-it-works.md` |
     | A `CONSTITUTION.template.md` section (add/renumber/retitle) | the section list, agent→section table, and per-section prose in `docs/constitution.md`; the "constitution sections" guidance in `docs/customizing.md` |
     | The autopilot phases or convergence cap | `how-it-works.md` Phase sections + `task-flows.md` Flow 1 |
     | The permission model | `docs/customizing.md` Part 1 + `docs/troubleshooting.md` permission section |

     `docs/` is **not** auto-propagated by `/forge-update` (it lives in the
     forge repo as the manual), so it will only stay correct if synced here,
     by hand, in the same commit. A docs-only sync that corrects drift is a
     PATCH; a docs change that adds a new manual page or capability is MINOR.

### Semver model for `.forge-version`

| Bump | Means | Examples |
| --- | --- | --- |
| **MAJOR (x)** | Breaking — existing projects must change something for `/forge-update` to work | Rename an agent · change CLARIFY/REJECT protocol · renumber CONSTITUTION sections · change pipeline order · remove an agent or command |
| **MINOR (y)** | New backwards-compatible capability — new projects get more, existing projects unaffected if they don't opt in | New agent · new slash command · new CONSTITUTION section · new `init-project` question · new scope-marker field · new routing-table row |
| **PATCH (z)** | Fix, cleanup, documentation — no new capability | Stale references · markdown linting · clarifying wording · tightening an existing forbidden action · revert to documented spec · cosmetic labels · de-numbering step references that drift |

**When a single commit mixes types, take the highest.** A commit that bundles
one new init-project question (MINOR) with four cleanup fixes (PATCH) is
MINOR. Prefer to NOT bundle — separate cleanup-only commits should stay
PATCH so the version doesn't inflate.

**MAJOR for the forge has never happened yet.** When it does, write a
migration guide under `docs/migrations/v<x>.0.0-<name>.md`, reference it
from the UPGRADING.md entry, and **mark that entry `⚠ BREAKING`** so
`/forge-update`'s Step 3.5b hard-stops and forces the user to confirm they
read the guide before applying.

**Declaring a project-owned prerequisite (`Requires`).** Whenever a
forge-owned change starts *assuming* something exists in the project that
`/forge-update` does not itself write — most commonly a `CONSTITUTION.md`
section that the version added only as a *manual step* — add a
`Requires (preflight)` list to that version's UPGRADING.md entry. Each item is
a self-contained `<project-file> must contain <pattern> — <why + remediation>`
assertion stating what the forge code needs present **right now**, never
referencing when the prerequisite was introduced. Re-declare inherited
requirements on every later version whose code still depends on them, so a
project upgrading from *below* the introducing version is still caught.
`/forge-update` Step 3.5a Greps the project for each and blocks apply on any
miss. This is the enforcement behind "MAJOR = existing projects must change
something" — without it, a skipped manual step only surfaces as a runtime
failure after the update lands.
