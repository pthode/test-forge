# agent-forge — Documentation

> **What this is:** the user manual for the multi-agent scaffold at the root of
> this repository. Explains what the scaffold does, how to set it up, how to
> use it day-to-day, and how to extend it.
>
> **Who this is for:** anyone who just used the agent-forge template to
> create a new product repo and wants to drive real work through it.

This is documentation, not the scaffold itself. The scaffold lives in `.claude/`
and `CLAUDE.md` at the repository root. Read those if you want to know what
Claude actually executes; read the files in this folder if you want to know
*how to drive the thing*.

---

## What is this scaffold?

A directory you open in [Claude Code](https://claude.com/claude-code) that
turns Claude from a single helpful assistant into a **structured multi-agent
pipeline**. Seventeen specialized agents (intake, spec architect, developer,
test engineer, doc writer, QA reviewer, security auditor, performance
analyst, database designer, DevOps engineer, code reviewer, UX consultant,
dependency auditor, refactor specialist, release engineer, observability
auditor, backlog curator) hand work to each other under written rules. A constitution file
pins per-project invariants. A locked-down permission model keeps the agents
contained to this repository.

You write one paragraph describing a feature you want built. The scaffold
runs intake → spec → code → tests → docs → reviewers → release, with explicit
gates and a convergence loop. You answer clarifying questions at one batched
window up front, then watch the rest run.

This is opinionated infrastructure. The opinions are documented in
[`intent.md`](intent.md).

### The flat layout

The scaffold uses a **flat repository layout**: the template clone is your
product repo. Scaffold files (`CLAUDE.md`, `.claude/`, `CONSTITUTION.md`,
this `docs/` folder) live at the repository root alongside the product's
own files (`/src/`, `/tests/`, `/docs/specs/`, etc.). One repo, one git
history, one `.gitignore`.

---

## Reading order

Eight files, in suggested order.

1. **[`intent.md`](intent.md)** — Philosophy. Why agents, why a pipeline,
   why a constitution. Trade-offs and problems solved. Read first if you
   want to know *whether* this scaffold fits your situation.
2. **[`getting-started.md`](getting-started.md)** — End-to-end setup:
   obtaining the scaffold (template / fork / clone), bootstrap path (fresh
   or existing repo), creating `.claude/settings.local.json`, filling the
   constitution, running your first feature.
3. **[`how-it-works.md`](how-it-works.md)** — Day-to-day operations
   manual: the two usage modes, the routing table, the four `/autopilot`
   phases, CLARIFY/REJECT protocol, convergence loop, and a full
   reference for all 17 agents.
4. **[`task-flows.md`](task-flows.md)** — The pipeline in motion. Sequence
   diagrams tracing six common task types (autopilot feature, bug fix,
   schema change, refactor, security-sensitive config, backlog grooming)
   through the agents, showing where work bounces back via CLARIFY/REJECT.
   Read it to build a mental model of the handoffs, or when an agent
   routed somewhere you didn't expect.
5. **[`constitution.md`](constitution.md)** — How `CONSTITUTION.md` works.
   What to fill before the first autopilot run. The §11 amendment process,
   the `CONSTITUTION.project.md` split (§11.2), backlog discipline (§12),
   versioning (§13). Why it overrides specs.
6. **[`customizing.md`](customizing.md)** — Two halves. First, the
   permission model (`.claude/settings.json`) — allow vs deny, deny
   precedence, what each deny category protects against. Second,
   extending the scaffold — adding new agents, modifying existing ones,
   writing custom slash commands, project constitution sections,
   stack-specific tooling.
7. **[`troubleshooting.md`](troubleshooting.md)** — Symptom-driven
   reference. Convergence stalls, prompt fatigue, agent loops, Windows
   gotchas.

(The eighth file is this `README.md` — the index you're reading.)

### Reference — not part of the main reading order

- **[`audit-prompt.md`](audit-prompt.md)** — A paste-ready prompt for
  running an independent expert-level audit of the scaffold (or your
  extended version of it). Use in a fresh Claude Code session, ideally
  in plan mode. Useful after substantial refactors, periodically as a
  quality check, or when onboarding a teammate who wants to verify the
  setup. Six audit dimensions covering correctness, software-engineering
  best practices, modern AI design, security, documentation, and
  AI/orchestration optimization.

---

## Quick start (10 minutes)

For the impatient. Full versions of each step in
[`getting-started.md`](getting-started.md).

1. **Get the scaffold** via "Use this template" on GitHub, fork, or plain
   `git clone`.
2. **Open the cloned repo in Claude Code.**
3. **Run `/init-project <product-name>`** — renames
   `CONSTITUTION.template.md` to `CONSTITUTION.md`, removes the template,
   updates `CLAUDE.md`'s `Product:` line.
4. **Fill `CONSTITUTION.md` §1 (Stack & boundaries).** Until §1 is
   non-`TBD`, the intake agent refuses to lock tickets — intentional. If
   latency-sensitive, fill §6 (Performance budgets) too.
5. **Create `.claude/settings.local.json`** with narrow allow rules for
   your stack's test, lint, and build commands. Workspace `settings.json`
   denies agents from creating this file; create by hand.
6. **Run `/autopilot <paragraph describing your first feature>`.** Intake
   batches clarifying questions; the rest runs autonomously.
7. **Review the artifacts** under the repository root: specs in
   `docs/specs/`, code in `src/`, tests in `tests/`, docs in `docs/api/`
   and the root `README.md`, QA / security / observability / release
   reports in `docs/<category>/`.

---

## What lives where

```
.                                # The product repo. Scaffold files and product files coexist.
├── CLAUDE.md                    # Router instructions Claude Code loads on entry.
├── CONSTITUTION.md              # Project invariants (filled in from template at bootstrap).
├── README.md                    # Welcome / product overview (replaced by doc-writer on
│                                #   first feature ship).
├── .gitignore                   # Includes settings.local.json + OS noise + stack build dirs.
├── .claude/
│   ├── settings.json            # Permission model (read-only to agents).
│   ├── settings.local.json      # Per-machine narrow allow rules (you create this).
│   ├── agents/                  # 17 agent definitions.
│   └── commands/                # /autopilot, /init-project.
├── docs/                        # Scaffold documentation AND per-feature artifacts.
│   ├── README.md                # This file.
│   ├── intent.md                # Philosophy.
│   ├── getting-started.md       # Setup walkthrough.
│   ├── how-it-works.md          # Operations manual + agents reference.
│   ├── task-flows.md            # Per-task-type sequence diagrams (the handoffs).
│   ├── constitution.md          # Filling and amending CONSTITUTION.md.
│   ├── customizing.md           # Permission model + extending the scaffold.
│   ├── troubleshooting.md       # Symptom-driven fixes.
│   ├── requirements/<feature>.md         # Locked tickets.
│   ├── specs/<feature>.md                # SDDs.
│   ├── api/, data-models/, diagrams/, schema/
│   ├── qa-reports/, security-reports/, observability-reports/
│   ├── perf-reports/, code-reviews/, ux-reviews/
│   ├── dependency-reports/, release-reports/, refactor-logs/
│   └── .autopilot-state/<feature>.json    # Convergence-loop state (tool state, not artifacts).
├── src/                         # Product code.
├── tests/                       # Unit + integration tests.
├── migrations/                  # Schema migrations (if your stack uses any).
└── infra/                       # IaC, k8s manifests, deploy workflows.
```

Scaffold artifacts and product artifacts share the same directory layout —
`docs/intent.md` is scaffold-provided manual content; `docs/specs/orders.md`
is product-specific spec output. They coexist because they answer different
questions about the same project.

---

## When the scaffold is the wrong tool

- **One-line changes.** A typo fix does not need orchestration. Use manual
  single-agent invocation (or just edit the file).
- **Spike code you plan to throw away.** Constitution + spec + observability
  discipline is overhead you don't need for a prototype. Use Claude Code
  without this scaffold.
- **Single-file scripts.** The scaffold assumes a project with `/src`,
  `/tests`, artifacts under `/docs`. For a 50-line utility, the structure
  fights you.
- **You disagree with the constitution's defaults and don't plan to amend
  them.** The constitution is load-bearing. Either amend it to match how
  you intend to work, or pick a different tool.

For features, bug fixes, refactors, schema changes, infra work,
documentation — the scaffold catches more issues earlier than ad-hoc
prompting does.

---

## Conventions used in this documentation

- **`/path/...`** with a leading slash refers to a path **at the repository
  root** (the convention used by agent definitions). So
  `/docs/specs/orders.md` means `docs/specs/orders.md` from the repo root.
- **`./path/...`** or paths without a leading slash refer to the same
  repository root.
- Slash commands appear as `/autopilot`, `/init-project`.
- Agent names appear as **`spec-architect`**, **`developer`**, etc.
- The reviewer trio in autopilot's Phase 3 is called the
  "convergence loop" — the fixpoint review iteration that runs until
  no new REJECTs surface.
