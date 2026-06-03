# How it works

> **What this covers:** the day-to-day operating model and reference for all
> 17 agents. Two usage modes, routing rules, the four autopilot phases,
> CLARIFY/REJECT protocol, convergence loop, and per-agent specifications
> (role, inputs, outputs, common rejections).
>
> **When to read it:** after `getting-started.md`, when you want to actually
> drive the pipeline. Also as reference when an agent rejects something and
> you need to understand why.

---

## Two ways to use the pipeline

There are exactly two modes. Don't invent a third.

### Mode 1 — `/autopilot <description>`

For new features and substantial changes. Runs all four phases (intake →
build → convergence → release) autonomously. You're in the loop only at
intake (clarifying questions) and at convergence/release escalations (if
they fire).

Use for: any change that adds behavior, modifies a contract, touches
multiple files, or needs more than one agent.

### Mode 2 — Manual single-agent invocation

For everything else: typo fixes, comment edits, log-level tweaks,
single-file bug fixes, refactors, one-off audits, ad-hoc questions.

You invoke one agent directly. No phases, no convergence loop, no
orchestration ceremony. The agent's own forbidden actions enforce the
right discipline:

- `developer` cannot write tests (`test-engineer`'s territory).
- `test-engineer` cannot modify `/src/` to make tests pass.
- `qa-reviewer` cannot edit anything (read-only by tool list).
- `security-auditor` cannot suppress findings.

For a bug fix that needs a regression test: invoke `developer` to fix,
then `test-engineer` to add a regression test (its rules require the test
to fail on pre-fix code), then optionally `qa-reviewer` to confirm.

---

## Routing table (which agent for which intent)

The router (Claude reading `CLAUDE.md`) matches your phrasing to an agent.

| When you say…                                            | Router invokes      |
|----------------------------------------------------------|---------------------|
| "I want", "build me", "I need a system", "feature"       | `requirements-intake` (then offers `/autopilot`) |
| "/autopilot", "autopilot this", "do the whole thing"     | enters **autopilot mode** |
| "design", "spec out", "API for X", "data model"          | `spec-architect`    |
| "implement", "build", "wire up", "write the code"        | `developer`         |
| "write tests", "add coverage", "TDD"                     | `test-engineer`     |
| "document", "README", "JSDoc", "changelog"               | `doc-writer`        |
| "ready to merge", "final review", "qa", "is this done"   | `qa-reviewer`       |
| "security review", "is this safe", "audit auth"          | `security-auditor`  |
| "slow", "optimize", "performance", "profile"             | `performance-analyst` |
| "migration", "schema", "add a column", "index"           | `database-designer` |
| "Dockerfile", "CI", "deploy", "pipeline", "infra"        | `devops-engineer`   |
| "review this code", "code smell", "clean this up"        | `code-reviewer`     |
| "accessibility", "a11y", "form UX", "frontend review"    | `ux-consultant`     |
| "audit packages", "CVE", "outdated deps", "license"      | `dependency-auditor` |
| "refactor", "rename", "extract", "inline"                | `refactor-specialist` |
| "release", "ship it", "deploy", "cut a release"          | `release-engineer`  |
| "observability review", "logging review", "event coverage" | `observability-auditor` |
| "groom the backlog", "review the backlog", "promote patterns", "is the backlog healthy" | `backlog-curator` |
| "tackle B-NNN", "work the backlog", "pick up a backlog item" | `refactor-specialist` (with the `B-NNN` ID) |
| "add to backlog", "defer this", "log as tech debt" | direct edit to `BACKLOG.md` by the orchestrator after confirming with you |

You can also invoke by name directly: "Run `security-auditor` on `src/auth/`."
When phrasing is ambiguous ("make this better"), the router asks before
dispatching.

The router does NOT write code, run tests, draft specs, or review work. It
**delegates**. If you see it doing the work itself — synthesizing a spec
inline, suggesting an implementation, writing tests in chat — it has
stepped out of its lane. Tell it to delegate.

---

## Autopilot mode — the four phases

```
/autopilot Build a /healthcheck endpoint that returns 200 OK with service
name, version, and timestamp.
```

The argument is either an inline description or a path to a requirements
file (`/autopilot docs/requests/foo.md`). If omitted, the orchestrator
asks "What do you want me to build?" once.

The orchestrator runs four phases in order.

### Phase 1 — Intake (the only user-interaction window)

`requirements-intake` drafts clarifying questions (typically 4–10) based
on your input. The orchestrator surfaces them via `AskUserQuestion`,
batched. You answer. The agent writes a locked ticket to
`/docs/requirements/<feature>.md` and signals `TICKET-LOCKED`.

After this, intake closes. The pipeline does not prompt again unless an
emergency escape fires.

### Phase 2 — Autonomous build

`spec-architect` writes the SDD, API contract, data model, and sequence
diagrams under `/docs/specs/`, `/docs/api/`, `/docs/data-models/`,
`/docs/diagrams/`.

Conditional specialists run in parallel:

- `database-designer` if persistence is touched.
- `devops-engineer` if infra is touched.
- `dependency-auditor` if a new direct dependency is added.

`developer` implements against the spec under `/src/`.

`test-engineer` writes unit + integration tests under `/tests/` derived
from the spec, runs the suite via Bash.

`doc-writer` writes the product README (replacing the scaffold welcome),
`docs/api/<feature>.md`, and inline docstrings.

### Phase 3 — Convergence loop

Reviewers run in parallel:

- `qa-reviewer` (always)
- `code-reviewer` (always)
- `observability-auditor` (always — constitution §8)
- `security-auditor` (when auth, input, secrets, crypto, network/file
  I/O, deserialization, SQL, or shell is touched)
- `performance-analyst` (when queries, loops, async, large data, or hot
  paths are touched)
- `ux-consultant` (when `/src/components`, `/pages`, `/app`, `/styles`
  is touched)
- `dependency-auditor` (when any dependency manifest was modified this
  iteration, or was modified during Phase 2 and not yet audited)

Each reviewer outputs a report and optionally `REJECT` blocks. The
orchestrator collects all REJECTs, routes them to the `TO:` agent named
in each, waits for fixes, re-runs the reviewers.

Loop terminates when **no `REJECT` blocks surface**.

**Smart cap.** The orchestrator computes a signature for each REJECT:
first 8 chars of `sha256(FROM + TO + SEVERITY + ARTIFACT + normalized(FINDINGS))`.
`normalized` strips whitespace and line numbers so a re-flagged finding
hashes identically across iterations.

Escalation fires when:

- A signature appears in **3 consecutive iterations** (no-progress).
- Total REJECT count did not decrease AND no signature changed.
- `iteration ≥ 8`.

On escalation, the orchestrator prints a recurring-findings summary and
stops. Second user-interaction window. Common pattern when this fires:
two reviewers contradict each other, and you need to amend the
constitution or update the spec to break the contradiction.

### Phase 4 — Release

After Phase 3 converges, `release-engineer` runs five gates:

1. **Source-control hygiene** — branch named `<type>/<slug>`, clean
   commit history.
2. **CI green** — `gh pr checks --watch`. A red CI triggers a REJECT to
   `developer` (impl bug), `test-engineer` (flaky test), or
   `devops-engineer` (pipeline-config failure).
3. **Deploy executed** — runs the documented deploy command. If interactive
   (production), surfaces an `URGENT: yes` CLARIFY.
4. **Smoke test passes** — exercises the primary requirement against the
   running deployment. A failing smoke test triggers rollback then a
   REJECT to `developer`.
5. **Observability footprint live** — queries the log store for each
   spec event; verifies alert rules reference runbooks.

Output: `/docs/release-reports/<feature>-<YYYY-MM-DD>.md` with verdict
`RELEASED` or `BLOCKED`.

### Workflow autonomy — who commits and merges (CONSTITUTION §14)

How far the orchestrator drives the `commit → push → PR → merge` path on its
own is set by **CONSTITUTION §14** (the project level, chosen at
`/init-project`) plus any stricter personal override — the effective level is
the stricter of the two. Three levels:

- **`review-all`** (default) — stop before every commit, PR, and merge.
- **`review-critical`** — autonomous on routine work; pause on critical
  changes (security-sensitive files, schema migrations, public API contracts,
  new dependencies).
- **`autonomous`** — drive commit → PR → merge within the floor.

A floor holds at every level and is never negotiable by this setting:
protected branches stay PR-only, the permission model is never loosened, CI
must be green before merge, and security-sensitive changes always get
explicit human confirmation. In autopilot, this is what decides whether
Phase 4 merges the PR or leaves it open for you. See
[`constitution.md`](constitution.md) §14 and `CLAUDE.md` "Workflow autonomy".

### State persistence (across the loops)

The orchestrator persists state to `/docs/.autopilot-state/<feature>.json`
so a killed session can resume. Schema:

```json
{
  "feature": "<slug>",
  "started_at": "<ISO-8601>",
  "status": "phase3_running" | "phase4_running" | "stalled" | "released" | "release_blocked",
  "iteration": 3,
  "signatures": {
    "a1b2c3d4": { "first_seen": 1, "last_seen": 3, "from": "qa-reviewer", "to": "developer", "severity": "blocker", "summary": "..." }
  }
}
```

`status` names the active phase. `iteration` is the current phase's
counter. `signatures` map starts fresh when Phase 3 → Phase 4 transition
happens.

### Final reports

**RELEASED:** comprehensive summary — built artifacts, test counts, QA
verdict, release details (branch, PR, CI, deploy target, smoke test,
observability events verified, rollback plan).

**BLOCKED:** Phase 3 artifacts, the blocker reason, the agent owning the
gap, recommended next step. A subsequent `/autopilot` resume picks up
from `status: release_blocked` and re-enters Phase 4.

---

## CLARIFY and REJECT — the handoff protocol

When an agent finds an ambiguity or a contradiction, it does not handle
it inline. It emits a structured block. The orchestrator routes the
block.

### CLARIFY — downstream agent finds an ambiguity

```
=== CLARIFY ===
FROM:    developer
TO:      spec-architect
RE:      spec R3 (authentication)
BLOCKED: yes
URGENT:  no

QUESTIONS:
  1. Spec R3 says "user is authenticated" but does not specify which auth
     method. JWT, session, both?

ASSUMPTION (only if BLOCKED: no):
  (none)
=== END CLARIFY ===
```

- `BLOCKED: yes` — emitter stopped, waiting on upstream.
- `BLOCKED: no` — emitter proceeded under an assumption (named below);
  upstream may override.
- `URGENT: yes` — requires the **user's** judgment (regulatory question,
  constitution conflict, scope discovery). Only signal that breaks the
  intake-closed rule in autopilot.

### REJECT — downstream work contradicts the spec or fails review

```
=== REJECT ===
FROM:     test-engineer
TO:       developer
SEVERITY: blocker
ARTIFACT: src/auth/login.ts:88

FINDINGS:
  - [blocker] Spec R4 requires 401 on invalid credentials, but
    login.ts:88 returns 400.

REQUIRED ACTION:
  Change to 401 with body { error: "invalid_credentials" } per
  /docs/api/auth.openapi.yaml.
=== END REJECT ===
```

Severities:

- `blocker` — must be fixed before pipeline advances.
- `major` — must be fixed before merge; pipeline may continue in parallel.
- `minor` — non-blocking; tracked in `/docs/qa-reports/`.

---

## Status reporting

The VS Code spinner shows generic words ("computing"). The orchestrator
prints explicit status lines:

**Before delegating:**

> → Starting **`<agent-name>`**: `<task summary>`. Expect `<1–3 min /
> 5–15 min / 15–30 min>`.

**When agent returns:**

> ✓ **`<agent-name>`** done — `<one-line summary>` — `<next step>`.

Silence for >30 seconds without an in-context-work announcement = nudge
the orchestrator.

---

## Artifact directory map

All paths resolve to the **repository root** (flat layout).

```
/docs/requirements/<feature>.md                       requirements-intake
/docs/specs/<feature>.md                              spec-architect
/docs/api/<feature>.openapi.yaml                      spec-architect
/docs/data-models/<feature>.md                        spec-architect
/docs/diagrams/<feature>.sequence.md                  spec-architect
/src/**                                               developer, refactor-specialist
/tests/unit/**, /tests/integration/**                 test-engineer
/README.md, /CHANGELOG.md, /docs/api/**               doc-writer
/docs/qa-reports/<feature>-<YYYY-MM-DD>.md            qa-reviewer
/docs/security-reports/<feature>-<YYYY-MM-DD>.md      security-auditor
/docs/perf-reports/<feature>-<YYYY-MM-DD>.md          performance-analyst
/migrations/**, /docs/schema/**                       database-designer
/Dockerfile, /.github/workflows/**, /infra/**         devops-engineer
/.env.example                                         devops-engineer
/docs/code-reviews/<feature>-<YYYY-MM-DD>.md          code-reviewer
/docs/ux-reviews/<feature>-<YYYY-MM-DD>.md            ux-consultant
/docs/dependency-reports/<YYYY-MM-DD>.md              dependency-auditor
/docs/refactor-logs/<scope>-<YYYY-MM-DD>.md           refactor-specialist
/docs/release-reports/<feature>-<YYYY-MM-DD>.md       release-engineer
/docs/observability-reports/<feature>-<YYYY-MM-DD>.md observability-auditor
/docs/backlog-reviews/<YYYY-MM-DD>.md                 backlog-curator
/BACKLOG.md                                           project-owned (appended by reviewers + refactor-specialist)
/CHANGELOG.md                                         project-owned (appended by doc-writer; version-rotated by release-engineer per §13)
```

`BACKLOG.md` and `CHANGELOG.md` are created by `/init-project`, not by a
single agent — they are project-owned ledgers that multiple agents append
to over the project's life. `CHANGELOG.md` exists only when the
constitution §13 versioning scheme is `semver`, `calver`, or `custom`
(not `none`). See [`constitution.md`](constitution.md) §12/§13.

---

## Agents reference

Each entry: **Role · Trigger phrases · Inputs · Outputs · Common
rejections · Forbidden actions · Tools**. Source of truth is each agent's
file under `.claude/agents/`; this page is a navigable summary.

### Phase 1 — Intake

#### `requirements-intake`

**Role.** Converts a raw user request into a locked requirements ticket.
Batches every clarifying question into a single user-interaction window.

**Triggers.** "I want", "build me", "I need a system", "feature request",
or any `/autopilot` start.

**Inputs.** Raw user prompt; constitution.

**Outputs.** `/docs/requirements/<feature>.md`.

**Modes.** Mode A (draft clarifying questions); Mode B (build the locked
ticket from answers). The orchestrator switches between them.

**Common emissions.** `SPLIT-REQUIRED` if the request bundles features
(asks the user which to run first). `URGENT: yes` CLARIFY if constitution
§1 is `TBD`.

**Forbidden.** Will not lock a ticket while §1 is `TBD`. Will not invent
answers to clarifying questions.

**Tools.** Read, Write, Grep, Glob.

### Phase 2 — Build

#### `spec-architect`

**Role.** Translates the ticket into precise, testable artifacts: SDD,
API contract (OpenAPI 3.1), data model, sequence diagrams.

**Triggers.** "design", "spec out", "API for X", "data model for Y",
"sequence diagram".

**Inputs.** Locked ticket; constitution (mandatory).

**Outputs.** `/docs/specs/<feature>.md` (always),
`/docs/api/<feature>.openapi.yaml` (HTTP API),
`/docs/data-models/<feature>.md` (persisted state),
`/docs/diagrams/<feature>.sequence.md` (>2 collaborators).

**Common rejections.** `URGENT: yes` CLARIFY if §1 or §6 is `TBD`.
Receives REJECTs from downstream; updates the spec rather than asking
downstream to work around.

**Forbidden.** Will not write code, tests, or end-user docs. Will not
make stack choices the constitution did not lock down.

**Tools.** Read, Write, Edit, MultiEdit, Grep, Glob.

#### `database-designer`

**Role.** Translates the data model into safe, reversible migrations.
Enforces two-phase migration discipline.

**Triggers.** "add a column", "new table", "migration", "schema change",
"index", "rename column".

**Inputs.** `/docs/data-models/<feature>.md`; constitution.

**Outputs.** `/migrations/<timestamp>_<verb>_<noun>.{sql,ts,py}` (paired
up/down); `/docs/schema/<table>.md` (updated, not appended).

**Common rejections.** CLARIFY to spec-architect when the data model is
incomplete (e.g., enum field without values).

**Forbidden.** Never drops or renames a column in the same migration
that stops writing it. Never adds NOT NULL without default or backfill
plan. Never uses `DROP TABLE` / `TRUNCATE` without explicit approval.

**Tools.** Read, Write, Edit, Bash, Grep, Glob.

#### `devops-engineer`

**Role.** Owns the path from source to production. Dockerfiles, CI/CD,
infrastructure-as-code, Kubernetes manifests, `.env.example`.

**Triggers.** "Dockerfile", "CI", "pipeline", "deploy", "infra",
"terraform", "k8s", "helm".

**Inputs.** Spec, ticket, application config; constitution.

**Outputs.** `/Dockerfile`, `/.dockerignore`, `/.github/workflows/*.yml`,
`/infra/**`, `/.env.example`; `/docs/deploy.md` for non-trivial topologies.

**Common rejections.** CLARIFY to developer when an env var is read by
code but undocumented. REJECT to spec-architect when the spec requires
infra contradicting the constitution.

**Forbidden.** Never bakes secrets into images. Never uses `:latest` or
unpinned base images. Never commits real `.env`, `*.pem`, `*.key`, etc.
Never disables signature verification.

**Tools.** Read, Write, Edit, Bash, Grep, Glob.

#### `dependency-auditor`

**Role.** Runs `npm audit` / `pip-audit` / `cargo audit` / `govulncheck`.
Flags outdated, abandoned, license issues, dev-in-prod leakage.

**Triggers.** "audit dependencies", "check packages", "CVE", "outdated",
"license check", or any dependency-manifest change.

**Inputs.** The project's dependency manifests; constitution.

**Outputs.** `/docs/dependency-reports/<YYYY-MM-DD>.md`.

**Common rejections.** REJECT to developer for any high-severity CVE in
a direct dependency.

**Forbidden.** Never auto-updates packages. Never suppresses findings
without explicit approval.

**Tools.** Read, Bash, Grep, Glob.

#### `developer`

**Role.** Implements what the spec describes. Writes production code
under `/src/`.

**Triggers.** "implement", "build", "wire up", "write the code".

**Inputs.** Ticket, SDD, API contract, data model, specialist outputs;
constitution.

**Outputs.** Source files under `/src/`.

**Common rejections.** CLARIFY to spec-architect when spec is ambiguous.
REJECT to spec-architect when spec contradicts constitution.

**Forbidden.** Will not write tests, README/CHANGELOG, or API docs. Will
not add behaviors not in the spec. Will not add error handling for
impossible cases.

**Tools.** Read, Write, Edit, Bash, Grep, Glob.

#### `test-engineer`

**Role.** Writes unit + integration tests **against the spec**, not
against the current implementation. Runs the full suite.

**Triggers.** "write tests", "add coverage", "TDD", "test this".

**Inputs.** Spec, ticket, source under `/src/`; constitution.

**Outputs.** `/tests/unit/**`, `/tests/integration/**`; chat summary of
pass/fail count, coverage, REJECTs emitted.

**Common rejections.** REJECT to developer when implementation
contradicts spec. REJECT to spec-architect when a ticket success
criterion has no spec requirement.

**Forbidden.** Will not modify `/src/` to make tests pass. Will not
write tests that assert what current code does without checking against
spec. Will not mock the system under test. Will not skip running the
suite.

**Tools.** Read, Write, Edit, Bash, Grep, Glob.

#### `doc-writer`

**Role.** Writes user-facing documentation: README, CHANGELOG, API docs,
JSDoc/TSDoc/docstring blocks.

**Triggers.** "document", "update the README", "write docs for", "add
JSDoc", "changelog entry".

**Inputs.** Spec, implementation, passing tests, ticket; constitution.

**Outputs.** `/README.md` (replaces scaffold welcome on first run),
`/CHANGELOG.md`, `/docs/api/<feature>.md`; inline docstrings.

**Common rejections.** CLARIFY to developer when behavior is unclear.

**Forbidden.** Will not modify `/src/` logic (docstring comment blocks
only). Will not modify `/tests/`. Will not invent behavior ("the system
will" — only "the system does"). Will not document private internals in
the public README.

**Tools.** Read, Write, Edit, Grep, Glob.

### Phase 3 — Convergence (reviewers)

#### `qa-reviewer`

**Role.** Final gate before merge. Read-only. Cross-checks ticket, spec,
implementation, tests, docs. Can emit REJECTs to any upstream agent.

**Triggers.** "ready to merge", "final review", "qa", "is this done".

**Inputs.** All previously produced artifacts; constitution.

**Outputs.** `/docs/qa-reports/<feature>-<YYYY-MM-DD>.md` with verdict,
coverage matrix, REJECT blocks, test-suite summary.

**Manual-mode tolerance.** When invoked outside `/autopilot`, some
artifacts may be missing (no ticket, no spec). Does not REJECT solely
on "ticket missing" — verifies against spec (if any) and constitution.

**Common rejections.** Spec/code mismatch → developer or spec-architect.
Spec/code match but no test → test-engineer. Code/README mismatch →
doc-writer. Constitution violation → blocker, route to owner.

**Forbidden.** Will not write, edit, or delete any file. Will not
re-design the spec.

**Tools.** Read, Bash, Grep, Glob.

#### `code-reviewer`

**Role.** Judges how code is written (quality), not whether it works
(correctness — that's QA / test-engineer). Read-only.

**Triggers.** "review this code", "is this clean", "code smell",
"refactor opportunities".

**Inputs.** The diff or changeset; constitution §3 (code style).

**Outputs.** `/docs/code-reviews/<feature>-<YYYY-MM-DD>.md`; chat summary
of top 3 issues.

**Severity tags.** `nit` (suggestion), `should-fix` (real quality issue),
`must-fix` (would harm maintainability).

**Common rejections.** None — doesn't emit REJECT (read-only quality
focus). Correctness issues spotted in passing go in `## Out of scope
(forward to qa-reviewer)`.

**Forbidden.** Will not comment on correctness or test coverage. Will
not modify code. Will not file `nit` without at least one
`should-fix`/`must-fix` in the same review.

**Tools.** Read, Grep, Glob.

#### `security-auditor`

**Role.** Finds security defects; reports them. Doesn't fix.

**Triggers.** "security review", "audit auth", "check for
vulnerabilities", "is this safe", "secrets check".

**Inputs.** Relevant code paths; constitution §5.

**Outputs.** `/docs/security-reports/<feature>-<YYYY-MM-DD>.md`.

**Severity.**

- `CRITICAL` — RCE, auth bypass, exposed secrets, unauthenticated data
  exfiltration.
- `HIGH` — privilege escalation, SQLi with limited data, stored XSS,
  missing CSRF, weak crypto (MD5/SHA1 for auth, ECB).
- `MEDIUM` — reflected XSS, verbose errors, missing security headers,
  outdated dep with HIGH CVE.
- `LOW` — best-practice violations without a concrete exploit.

**Common rejections.** REJECT to developer for every CRITICAL or HIGH.
REJECT to spec-architect if spec contradicts §5.

**Forbidden.** Will not modify code. Will not skip dependency audit.
Will not suppress or downgrade a finding without written justification.

**Tools.** Read, Bash, Grep, Glob.

#### `performance-analyst`

**Role.** Finds concrete, measurable performance defects. Doesn't
speculate.

**Triggers.** "slow", "optimize", "profile", "performance", "p99",
"scale".

**Inputs.** Implementation; constitution §6 (when present, that is the
baseline; when `TBD`, falls back to structural checks).

**Outputs.** `/docs/perf-reports/<feature>-<YYYY-MM-DD>.md`.

**Patterns flagged.**

1. N+1 queries.
2. Missing indexes on query predicates.
3. Unbounded loops / recursion on user-supplied data.
4. Blocking calls in async contexts.

**Common rejections.** REJECT to developer for measurable blockers.
Speculative findings are NOT filed.

**Forbidden.** Will not modify code. Will not file micro-optimizations
without a benchmark. Will not speculate about future scale.

**Tools.** Read, Bash, Grep, Glob.

#### `ux-consultant`

**Role.** Judges user-facing surface for accessibility and interaction
quality. Read-only. Frontend only.

**Triggers.** "frontend review", "UI", "accessibility", "a11y", "form
UX", or any diff under `/src/components`, `/pages`, `/app`, `/styles`.

**Inputs.** Frontend code; constitution §7.

**Outputs.** `/docs/ux-reviews/<feature>-<YYYY-MM-DD>.md`.

**Severity tags.** `blocker` (WCAG-A, keyboard inaccess, focus traps,
missing labels), `should-fix` (WCAG-AA, missing error/loading states),
`nice-to-have` (polish, reduced-motion).

**Common rejections.** No REJECT (read-only). Blocker-severity items in
chat summary so orchestrator routes a fix to developer.

**Forbidden.** Will not modify code. Will not file findings outside
frontend. Will not use subjective taste — only objective standards.

**Tools.** Read, Grep, Glob.

#### `observability-auditor`

**Role.** Verifies the code can be operated. Every spec success criterion
and failure mode has a corresponding structured log event. Levels
calibrated. No PII in payloads. Alerts have runbooks.

**Triggers.** "observability review", "logging review", "are we logging
this", "event coverage check".

**Inputs.** Spec, implementation; constitution §8 (job description).

**Outputs.** `/docs/observability-reports/<feature>-<YYYY-MM-DD>.md`.

**Severity.**

- `blocker` — spec success/failure has no event; PII/secrets logged;
  alert without runbook.
- `major` — log-level misuse on high-traffic path; trace ID missing in
  multi-service flow; hardcoded event names across multiple sites.
- `minor` — missing field; metric naming inconsistent; alert threshold
  off.

**Common rejections.** REJECT to developer for missing events,
hardcoded event names, log-level misuse, missing trace propagation.
REJECT to devops-engineer for missing metrics, missing alerts, alerts
without runbooks.

**Forbidden.** Will not modify source. Will not file a finding without
citing the spec/event mapping that's missing or wrong.

**Tools.** Read, Bash, Grep, Glob.

### Phase 4 — Release

#### `release-engineer`

**Role.** Takes an approved change from green CI to verified-running
production. Five gates: source-control, CI, deploy, smoke, observability.

**Triggers.** "release", "ship it", "deploy", "cut a release", or
autopilot's Phase 4.

**Inputs.** Approved code, ticket, spec, tests, QA report, security
report, observability report; constitution.

**Outputs.** `/docs/release-reports/<feature>-<YYYY-MM-DD>.md` with
verdict; `/docs/release-reports/<feature>-deploy-runbook.md` if
automation is missing.

**Detected deploy mechanism.** Looks for `.github/workflows/deploy*.yml`,
`infra/`, `Makefile` deploy targets, `flyctl`, `vercel`, `kubectl`. Does
not invent one.

**Common rejections.**

- CI test failure → developer or test-engineer.
- CI pipeline-config failure → devops-engineer.
- Missing deploy mechanism → `URGENT: yes` BLOCKED CLARIFY to user.
- Missing log store / metrics / alert rule → devops-engineer.
- Missing rollback for destructive schema change → database-designer.
- Smoke test fails → execute rollback, then REJECT to developer.

**Forbidden.** Will not merge the PR unless explicitly delegated. Will
not force-push to shared branches. Will not deploy while CI is red.
Will not mark "complete" while smoke/observability/rollback are missing.
Will not invent CI/deploy/infra the project hasn't configured.

**Tools.** Read, Write, Edit, Bash, Grep, Glob.

### Standalone specialists

#### `refactor-specialist`

**Role.** Behavior-preserving refactors only. Writes characterization
tests first. One change at a time. Runs full suite after each. Reverts
on red.

**Triggers.** "refactor", "rename", "extract method", "inline",
"untangle", "clean this up without changing behavior".

**Inputs.** The scope to refactor; full test suite must pass green
before starting.

**Outputs.** Source under `/src/`;
`/docs/refactor-logs/<scope>-<YYYY-MM-DD>.md`.

**Forbidden.** Not for bug fixes, performance, or feature work — those
route elsewhere. Will not skip characterization-tests-first. Will not
make multiple changes between test runs.

**Tools.** Read, Write, Edit, Bash, Grep, Glob.

#### `backlog-curator`

**Role.** Read-only grooming of `BACKLOG.md`. Reviewers fill the backlog
one entry at a time during pipeline runs and cannot see across sessions;
the curator reads the whole thing and finds the cross-session patterns no
single reviewer could spot. Produces a proposal report; executes nothing.

**Triggers.** "groom the backlog", "review the backlog", "any patterns we
should promote", "is the backlog healthy", or scheduled `/loop`
invocations.

**Inputs.** `/BACKLOG.md`; constitution §12 (Backlog discipline — defines
the severity model and grooming responsibilities it acts on).

**Outputs.** `/docs/backlog-reviews/<YYYY-MM-DD>.md` — health metrics,
systemic warnings, proposed minor→major consolidations, proposed stale-
singleton archivals, past-deadline list.

**What it proposes.**

- **Consolidation (minor→major)** when ≥3 active entries of the same
  `Type` share a token cluster in their `Suggested fix`. Cites every
  contributing `B-NNN` ID.
- **Archival** of active `minor` entries older than 180 days that never
  joined a pattern (never auto-archives `tech-debt` or
  `observability-gap` without explicit override).
- **Systemic warning** when one `Type` exceeds 30% of active entries.
- **Past-deadline visibility** — entries the orchestrator will promote to
  `major` on the next pipeline run per §12.3.

**Common emissions.** `URGENT: yes` CLARIFY if §12 is missing or `TBD`
(grooming requires the discipline to be locked). CLARIFY to the
orchestrator when a backlog entry is malformed against §12.1. Emits no
REJECT (read-only, advisory).

**Forbidden.** Will not modify `BACKLOG.md` or any artifact (tool list is
Read/Grep/Glob). Will not apply its own proposals — `refactor-specialist`
or the orchestrator applies on user approval. Will not propose a
consolidation with fewer than 3 contributing entries. Will not invent
entries that don't exist in the backlog.

**Tools.** Read, Grep, Glob.

---

## Pipeline at a glance

```
Phase 1 (intake):       requirements-intake
Phase 2 (build):        spec-architect → developer → test-engineer → doc-writer
                        (parallel: database-designer, devops-engineer,
                         dependency-auditor as applicable)
Phase 3 (convergence):  qa-reviewer + code-reviewer + observability-auditor
                        (always)
                        security-auditor / performance-analyst /
                        ux-consultant / dependency-auditor (when applicable)
Phase 4 (release):      release-engineer

Standalone:             refactor-specialist, backlog-curator
```

For each agent's full definition, read its file under `.claude/agents/`.
For customizing or extending the pipeline, see
[`customizing.md`](customizing.md).
