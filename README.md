# agent-forge template

You cloned the **agent-forge template**. This repo IS your product repo — the scaffold's files come with it, the product code grows alongside them, and everything lives in one git history.

> This file is the scaffold's welcome page. It points you at the canonical bootstrap instructions in [`CLAUDE.md`](CLAUDE.md). After you ship your first feature, the README you read here is replaced — `/init-project` writes a small stub, and `doc-writer` expands it into your product's own README as the project grows.

---

## What is this?

A multi-agent scaffold for [Claude Code](https://claude.com/claude-code) that takes a software feature from raw idea to verified production deployment, with structured handoffs, convergence-loop reviews, and explicit gates at every stage.

Roughly sixteen specialized agents (intake, spec architect, developer, test engineer, doc writer, QA reviewer, security auditor, performance analyst, database designer, DevOps engineer, code reviewer, UX consultant, dependency auditor, refactor specialist, release engineer, observability auditor) hand work to each other under written rules. A constitution file pins per-project invariants. A locked-down permission model keeps the agents contained to this repository.

You write one paragraph describing a feature. The scaffold runs intake → spec → code → tests → docs → reviewers → release, with explicit gates and a convergence loop. You answer clarifying questions at one batched window up front, then watch the rest run.

---

## Quick start

The canonical, always-current bootstrap procedure lives in [`CLAUDE.md`](CLAUDE.md) under **"Bootstrapping this template"**. Read that section. The short version:

1. Run `/init-project <product-name>`. The command handles the rename of `CONSTITUTION.template.md` to `CONSTITUTION.md`, cleans up forge-internal docs, writes a project stub `README.md` and a `CONTRIBUTING.md`, sets up `CLAUDE.project.md`, asks you about monitoring scope (audit / analytics / security) and test strategy (local isolation / cloud policy / E2E scope), and prints a final next-step checklist.
2. Follow that checklist — at minimum fill `CONSTITUTION.md` §1 (Stack & boundaries) and create `.claude/settings.local.json` with narrow allow rules for your stack.
3. Run `/autopilot <description of your first feature>`. Intake batches clarifying questions up front; the rest of the pipeline runs to completion unless an urgent escape fires.

For details on every step — including the security rationale behind the permission model, the constitution's role, and how `/forge-update` keeps you in sync with upstream — see [`CLAUDE.md`](CLAUDE.md).

---

## How the pipeline works (high level)

```
              ┌─────────────────────────────────────────────┐
              │           Phase 1 — Intake                  │
              │   requirements-intake (interviews user)     │
              │   → /docs/requirements/<feature>.md         │
              └─────────────────────┬───────────────────────┘
                                    │
              ┌─────────────────────▼───────────────────────┐
              │           Phase 2 — Build                   │
              │  spec-architect → developer → test-engineer │
              │              → doc-writer                   │
              │  (+ parallel: database-designer,            │
              │   devops-engineer, dependency-auditor)      │
              └─────────────────────┬───────────────────────┘
                                    │
              ┌─────────────────────▼───────────────────────┐
              │   Phase 3 — Convergence loop (fixpoint)     │
              │   parallel reviewers:                       │
              │     qa-reviewer (always)                    │
              │     code-reviewer (always)                  │
              │     observability-auditor (always)          │
              │     security-auditor (when applicable)      │
              │     performance-analyst (when applicable)   │
              │     ux-consultant (when applicable)         │
              │   REJECTs route automatically until clean   │
              │   (smart cap: 3 recurring signatures or     │
              │    no-progress or 8 iterations → escalate)  │
              └─────────────────────┬───────────────────────┘
                                    │
              ┌─────────────────────▼───────────────────────┐
              │           Phase 4 — Release                 │
              │  release-engineer runs five gates:          │
              │   source-control hygiene → CI green →       │
              │   deploy → smoke test → observability       │
              └─────────────────────────────────────────────┘
```

---

## When NOT to use autopilot

Autopilot is the right tool for new features and substantial changes. For everything else — typo fixes, comment edits, log-level tweaks, single-file bug fixes, refactors, audits — use **manual single-agent invocation**. Invoke `developer`, `code-reviewer`, `security-auditor`, `refactor-specialist`, etc. directly. The agents' own forbidden actions enforce the right discipline; the pipeline ceremony is unnecessary for one-shot work.

For a bug that needs a regression test: invoke `developer` to fix, then `test-engineer` to add the regression test (the agent's rules require it to fail on pre-fix code), then optionally `qa-reviewer` to confirm.

---

## Why a constitution?

Every project has invariants that survive across features — stack decisions, non-negotiables, code style, test discipline, security posture, performance budgets, a11y baseline, observability rules, DoD. Without a written record, every spec re-derives these from scratch and they drift.

The constitution is upstream of everything: `Constitution > Spec > Implementation > Tests > Docs`. Agents reading the constitution alongside the spec catch a contradictory spec before they implement it.

Amendments go through a documented process (`CONSTITUTION.md` §11), not ad-hoc PR exceptions.

---

## See also

- [`CLAUDE.md`](CLAUDE.md) — the router playbook. Canonical source of routing rules, pipeline order, autopilot mode, bootstrapping, and the path-resolution rules every agent obeys.
- [`UPGRADING.md`](UPGRADING.md) — per-version migration guide. Drives `/forge-update`.
- [`.claude/commands/autopilot.md`](.claude/commands/autopilot.md) — the autopilot orchestration algorithm (intake → build → convergence → release).
- Each agent definition under [`.claude/agents/`](.claude/agents/) — full responsibilities, forbidden actions, output artifacts, and the structured-block protocol (CLARIFY / REJECT).
