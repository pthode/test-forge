# The constitution

> **What this covers:** what `CONSTITUTION.md` is, why it exists, how
> agents use it, what to fill in before the first `/autopilot` run, and how to
> amend it later.
>
> **When to read it:** right after `/init-project`, before you fill in §1. Or
> when an agent rejects work citing the constitution and you want to understand
> the rule it is enforcing.

The constitution is the **highest-precedence document** in the scaffold:

> **Constitution > Spec > Implementation > Tests > Docs.**

A spec that contradicts the constitution is wrong. An implementation that
contradicts the spec is wrong. The hierarchy is enforced by every agent — when
two artifacts disagree, the higher one wins, and the agent rejects upstream
to fix the higher artifact rather than working around it.

This document explains how to make that machinery work for you.

---

## What the constitution is

A markdown file at the repository root (`/CONSTITUTION.md`), filled in from
`CONSTITUTION.template.md` by `/init-project` (which renames the template
to `CONSTITUTION.md` and removes the template). It defines **project-level
invariants that survive across features**:

1. Stack & boundaries (§1)
2. Non-negotiables (§2)
3. Code style anchors (§3)
4. Test discipline (§4)
5. Security posture (§5)
6. Performance budgets (§6)
7. Accessibility & UX baseline (§7)
8. Monitoring & observability (§8)
9. Definition of Done (§9)
10. Branching, commits, PR hygiene (§10)
11. Amendment process (§11) — split into §11.1 (amending forge-owned
    sections) and §11.2 (project-specific extensions)
12. Backlog discipline (§12)
13. Release & versioning (§13)
14. Workflow autonomy (§14)

Sections §1–§14 are **forge-owned** — they ship with the scaffold and
`/forge-update` may add §15, §16, … in future versions. Project-specific
invariants you add yourself live in a **separate** file,
`CONSTITUTION.project.md`, using `§P1`, `§P2`, … numbering (see
"Project-specific extensions" below). The template is opinionated; most
projects adopt the defaults verbatim and only customize §1, §6, §13, §14,
and possibly §3.

---

## What the constitution is **not**

- **It is not the project's full documentation.** Operational runbooks,
  release notes, ADRs, postmortems, onboarding guides — those live elsewhere.
- **It is not a spec.** A spec describes one feature in detail; the
  constitution describes invariants that apply to every feature.
- **It is not optional once filled in.** A "constitution we wrote but do not
  follow" is worse than no constitution. The agents enforce it; if you do not
  want a rule enforced, amend it out.

---

## How agents use the constitution

Every agent that produces an artifact is required to read the constitution
**before** writing. The agent's definition file (under `.claude/agents/`)
spells out exactly which sections bind it:

| Agent | Constitution sections it reads |
|-------|--------------------------------|
| `spec-architect` | §1, §2, §6, §7 — and the rest if the spec touches them |
| `developer` | §1 stack, §2 non-negotiables, §3 style, §5 security, §6 perf, §8 observability, §9 DoD |
| `test-engineer` | §4 (test discipline) |
| `doc-writer` | §1 stack, §3 style, §9 DoD, §13.3 changelog |
| `database-designer` | §1 stack, §2 non-negotiables, §6 perf, §9 DoD |
| `devops-engineer` | §1 stack, §2.7 deploy/observability/rollback, §5 security, §8 observability, §9 DoD |
| `security-auditor` | §5 (this section IS the agent's baseline) |
| `performance-analyst` | §6 (this section IS the agent's baseline) |
| `code-reviewer` | §3 (code style anchors) |
| `ux-consultant` | §7 (accessibility & UX baseline) |
| `observability-auditor` | §8 (this section IS the agent's job description) |
| `qa-reviewer` | All of it — final cross-check (incl. §11.2 project-section conflicts) |
| `release-engineer` | §2.7, §9, §10, §13 (versioning & changelog rotation), §14 (PR-merge gating) |
| `backlog-curator` | §12 (backlog discipline — its severity model and grooming rules) |

The mechanism: each agent's definition includes a "Constitution precedence"
rule that says (in effect) *read CONSTITUTION.md, treat it as binding, and if
the spec contradicts a non-`TBD` section of the constitution, emit a REJECT
to `spec-architect` instead of implementing the contradiction.*

This is what makes the constitution actually load-bearing rather than
ceremonial.

---

## Sections that **must** be filled before `/autopilot` runs

### §1. Stack & boundaries — required, always

The template's §1 starts as `_TBD_` in every field:

```markdown
- **Language(s) & runtime:** _TBD_
- **Framework(s):** _TBD_
- **Datastore(s):** _TBD_
- **External services we depend on:** _TBD_
- **Deployment target:** _TBD_
- **Supported clients / browsers / OSs:** _TBD_
```

Replace each `_TBD_` with a concrete answer. Until you do, `spec-architect`
emits an `URGENT: yes` CLARIFY at the start of every pipeline run, surfacing
the gap. The agent **will not guess** at the stack — that is one of the
most damaging mistakes an autonomous pipeline can make, and the constitution
discipline blocks it explicitly.

What "concrete" means: another engineer (or another instance of Claude, six
months from now) should be able to read your §1 and pick the right
dependency on the first try.

Bad:

```markdown
- **Language(s) & runtime:** TypeScript.
```

Good:

```markdown
- **Language(s) & runtime:** TypeScript 5.x targeting Node 20 LTS. Strict
  mode (`"strict": true`) in `tsconfig.json`. No ts-ignore in `main`.
```

Bad:

```markdown
- **Datastore(s):** Postgres.
```

Good:

```markdown
- **Datastore(s):** PostgreSQL 16 primary (managed by Supabase). Redis 7
  for ephemeral state (queues, rate-limit counters). No other persistent
  stores — if you reach for one, that is a §11 amendment.
```

### §6. Performance budgets — required for latency-sensitive projects

If your project is user-facing and latency-sensitive (any HTTP API serving
real-time requests, any oncall-paged service), fill these:

```markdown
- **p95 request latency:** 200 ms
- **p99 request latency:** 800 ms
- **Cold-start budget:** 2000 ms
- **Memory ceiling per instance:** 512 MB
- **DB queries per request (steady state):** ≤ 5
```

`performance-analyst` uses these to flag budget violations. Without them,
the agent falls back to structural checks (N+1 queries, unbounded loops)
and notes in its report that no budgets were declared.

If your project is **not** latency-sensitive (a CLI tool, a static-site
generator, an internal batch job), leave §6 as `TBD`. That is fine.

---

## Sections you usually leave at template defaults

The template is opinionated for a reason. Most projects benefit from these
defaults verbatim.

### §2. Non-negotiables

Seven rules that override convenience:

1. No secrets in code or images.
2. No destructive migrations in a single deploy (two-phase: add → backfill →
   flip → remove).
3. No silent data loss (any path that drops, truncates, or coerces user
   data must log + surface the loss).
4. No unauthenticated mutation endpoints.
5. No `// TODO` left in `main`.
6. No vendored copies of third-party code without `dependency-auditor`
   sign-off.
7. No deploy without observability footprint (§8) and rollback path
   (§9 DoD).

If you genuinely disagree with one (e.g., "we vendor critical deps because
of supply-chain concerns" might amend §2.6), use the §11 amendment process.

### §3. Code style anchors

Naming, function cohesion, comment philosophy, error-handling style,
import style, formatter discipline. These shape how `code-reviewer`
evaluates new code.

The default §3 is language-agnostic. If your stack benefits from
language-specific anchors ("Go errors are always values, never panicked
across module boundaries"; "Python: prefer `dataclass` over `pydantic` for
internal types"), add them here.

### §4. Test discipline

Spec-derived tests, test pyramid, no mocks of code you own, no DB mocks in
integration tests, no flaky tests, coverage floor.

You may want to set the coverage floor:

```markdown
- **Coverage floor:** 80%.
```

Coverage is a smoke alarm, not a goal — but a smoke alarm with no threshold
is no alarm at all.

### §5. Security posture

Input is hostile, authn ≠ authz, least privilege, no hand-rolled crypto,
dependencies need auditor sign-off, no PII / secrets in logs.

The template's §5 is the floor for production software. If you have
additional requirements (HIPAA, PCI-DSS, SOC 2), append them.

### §7. Accessibility & UX baseline

WCAG 2.2 AA floor, keyboard-first, no color-only signaling,
loading/empty/error states are first-class, form errors next to the field
and survive refresh.

Backend-only projects can mark §7 as `N/A`. Frontend projects should leave
defaults unless the user research demands more.

### §8. Observability & event logging

Every business-meaningful state change emits one structured log line.
Stable event names from a code-level enum/const. No PII / secrets in
payloads. Correlation IDs propagate. Log levels calibrated. Every spec
success criterion and failure mode has a logged event. Alerts have
runbooks.

The default §8 is the floor for any production service. Leave defaults.

### §9. Definition of Done

A checklist that says when a change is actually shippable:

- [ ] Spec exists under `/docs/specs/` and matches the implementation.
- [ ] Implementation compiles / type-checks / lints clean.
- [ ] Tests added or updated; full suite green locally **and in CI**.
- [ ] Docs reflect the change.
- [ ] Migrations (if any) are reversible and two-phase.
- [ ] `security-auditor` reviewed (or explicitly waived as non-applicable).
- [ ] `observability-auditor` confirms each spec event/failure-mode has a
  logged counterpart.
- [ ] Monitoring / alert rules updated for new endpoints or workers.
- [ ] Rollback path documented.
- [ ] `qa-reviewer` accepted.
- [ ] No `blocker` or `major` items open against the change.

`qa-reviewer` checks each box at the convergence loop. A red box is a
REJECT.

### §10. Branching, commits, PR hygiene

Branch from main, one concern per PR, imperative commit messages, no force
push to shared branches, green CI before merge.

`release-engineer` enforces these.

### §12. Backlog discipline

The pipeline defaults to **fix-now**, not "we'll get to it." Every finding
that surfaces during review has exactly three landing places, by severity:

- **`blocker`** — fix before convergence closes. No exceptions.
- **`major`** — fix before convergence closes by default; may defer to the
  backlog only with an explicit user decision and a written reason.
- **`minor`** — *always* logged to `BACKLOG.md`, never fixed inline in the
  same iteration. Reviewer-internal labels (`nit`, `nice-to-have`, `LOW`)
  all map to `minor` and all go to the backlog.

The stratification stops reviewers from smuggling "should really be done
now" work through as `minor`. If they want it this iteration, they classify
it `major` or `blocker` and own that call.

`BACKLOG.md` lives at the repo root, is created by `/init-project`, and is
project-owned (`/forge-update` never touches it). Entries are `B-NNN` with a
`Type`, `Severity`, `Suggested fix`, and a `Deadline` (default 90 days).
Four mechanisms keep it from becoming a graveyard (§12.3): `refactor-specialist`
accepts a `B-NNN` ID directly ("tackle B-007"); `backlog-curator` proposes
minor→major consolidations and stale-singleton archivals; one `Type`
exceeding 30% of the backlog raises a systemic warning; and past-deadline
entries promote to `major` findings on the next pipeline run. Any run that
adds ≥5 backlog entries in one iteration surfaces a tech-debt-tail warning
in the release report (§12.5).

See [`how-it-works.md`](how-it-works.md) for the `backlog-curator` agent
reference and the routing rows that drive backlog work.

### §13. Release & versioning

Declares how the project numbers releases. `/init-project` asks a versioning
question and fills §13 from the answer. Four schemes:

- **`semver`** (`MAJOR.MINOR.PATCH`) — libraries, SDKs, CLIs. Communicates
  *what changed* in compatibility terms.
- **`calver`** (`YYYY.MM.MICRO`) — apps, services, internal tools.
  Communicates *when*, not what.
- **`none`** — continuous-deployment services. No version numbers; the git
  commit hash is the history. `CHANGELOG.md` is not maintained.
- **`custom`** — describe the scheme in §13.2 by hand.

The scheme drives two agents. `doc-writer` appends every feature's
user-visible changes to the `## [Unreleased]` section of `CHANGELOG.md`
(Keep-a-Changelog format), unless the scheme is `none`. `release-engineer`
(Gate 1) bumps the version field at §13.1's declared manifest path, rotates
`Unreleased` into `[<new-version>] — <date>`, and creates an immutable
`v<version>` git tag on merge — or skips all of it when the scheme is
`none`. If §13.1's version-field location is `_TBD_` under a non-`none`
scheme, `release-engineer` CLARIFY-blocks rather than guessing.

`CHANGELOG.md` exists at the repo root only when the scheme is `semver`,
`calver`, or `custom`. Like `BACKLOG.md`, it is project-owned and
`/forge-update` never touches it.

### §14. Workflow autonomy

Declares how much of the `commit → push → PR → merge` path the orchestrator
drives on its own versus pausing for human review. Layered like the
permission model: a fixed floor plus a configurable level.

The **floor** (§14.1) never moves: protected branches (`main` / `release/*`)
are PR-only, the permission model is never loosened, CI must be green before
merge, and security-sensitive changes always get explicit human confirmation
— at every level.

The **level** (§14.2), set by `/init-project`, is one of:

- **`review-all`** — pause before every commit, PR, and merge. The default,
  identical to having no setting; nothing lands without a human `ok`.
- **`review-critical`** — autonomous on routine work; pause only on critical
  changes (§14.4: security-sensitive set, schema migrations, public API
  contracts, new dependencies).
- **`autonomous`** — drive `commit → push → PR → merge` within the floor;
  surface only `URGENT` and the security-sensitive confirmation.

A contributor may set a **personal override** (§14.5) that is *stricter*
than the project level — never looser; the orchestrator uses the stricter of
the two. Unlike §1's stack, §14 is never a `TBD` blocker: its safe default
(`review-all`) lets the pipeline run even if init's autonomy question was
skipped.

Unlike most sections, §14 is read by the **orchestrator (the `CLAUDE.md`
router) itself** — it decides when to pause — and it gates
`release-engineer`'s PR-merge step in autopilot Phase 4. It is not owned by
a single pipeline agent.

---

## Project-specific extensions (`CONSTITUTION.project.md`)

Sections §1–§14 are forge-owned. As the scaffold evolves it may add §15,
§16, … in future versions, so **projects must not occupy that numerical
range.** When you need invariants beyond what the forge provides
(compliance, i18n, ML-data governance, a house architecture rule), they go
in a separate file — never as a hand-added §15 in `CONSTITUTION.md`.

This mirrors the `CLAUDE.md` / `CLAUDE.project.md` split (§11.2):

| | Forge-owned | Project-owned |
|---|---|---|
| **File** | `CONSTITUTION.md` | `CONSTITUTION.project.md` |
| **Sections** | §1–§14 (and future §15, §16, …) | `§P1`, `§P2`, `§P3`, … |
| **Created by** | `/init-project` (from the template) | `/init-project` (empty stub) |
| **Touched by `/forge-update`** | yes | never |

The `§P` prefix is permanent — projects never use bare numbers, the forge
never uses `§P*` — so no future numerical addition can collide.

**Hard rules for the project file:**

- **Additive only.** A `§P` section may add a stricter or additional rule.
  It may **not** contradict or override any §1–§14 forge section. To change
  a forge section, amend it via §11.1.
- **Read alongside the forge file.** Every agent that reads
  `/CONSTITUTION.md` MUST also read `/CONSTITUTION.project.md` if it exists.
  The forge file is the base; the project file extends it.
- **Cited by `§P` prefix.** Agent reports and PRs say "violated §P2" vs.
  "violated §4" so the owner of each rule is unambiguous.
- **A contradicting `§P` section is a `qa-reviewer` blocker.** The fix is
  either a §11.1 amendment to the forge section, or removing the
  contradicting project rule.

`/init-project` creates `CONSTITUTION.project.md` as an empty stub with the
convention documented inline; `/forge-update` leaves it untouched on every
upgrade. That separation is what lets the forge ship new `CONSTITUTION.md`
versions without ever clobbering your project's own invariants.

---

## Worked example: filling §1 for a Node service

Starting from the template:

```markdown
## 1. Stack & boundaries

- **Language(s) & runtime:** _TBD_
- **Framework(s):** _TBD_
- **Datastore(s):** _TBD_
- **External services we depend on:** _TBD_
- **Deployment target:** _TBD_
- **Supported clients / browsers / OSs:** _TBD_
```

After filling:

```markdown
## 1. Stack & boundaries

- **Language(s) & runtime:** TypeScript 5.4 targeting Node 20 LTS. Strict
  mode on; `noUncheckedIndexedAccess` enabled. No `any` in committed code
  (use `unknown` and narrow). ESM modules, not CommonJS.
- **Framework(s):** Fastify 4.x (HTTP), Prisma 5.x (ORM), Zod 3.x (input
  validation), Vitest 1.x (test runner), Pino (structured logging).
- **Datastore(s):** PostgreSQL 16 primary (Supabase-managed). Redis 7 for
  short-lived state (rate-limit counters, idempotency keys). No other
  persistent stores; reaching for one is a §11 amendment.
- **External services we depend on:** Stripe (payments), Resend (email),
  Sentry (errors), GitHub (auth via OAuth).
- **Deployment target:** Fly.io. Single region (`fra`) for v1; multi-region
  failover is on the roadmap and will trigger a §11 amendment when added.
- **Supported clients / browsers / OSs:** modern evergreen browsers
  (last 2 majors of Chrome, Firefox, Safari, Edge). Mobile WebKit on
  iOS 16+. No IE11. No legacy Edge.
```

Notes on the filled version:

- Every choice is **concrete**: a major version, not "TypeScript". `strict`
  mode is explicit, not implied.
- The "no other persistent stores" line is a constraint, not a description.
  Future agents will reject specs that introduce a third datastore without
  a §11 amendment.
- The "multi-region failover triggers an amendment" line is a forward-looking
  invariant — it documents that a change to the deployment topology is
  significant enough to require process, not just code.

This is the level of detail that makes §1 load-bearing.

---

## Amending the constitution (§11.1)

The constitution is amended, **not** overridden inline. There is no "this
PR is an exception" clause. This is the **§11.1** process — amending a
forge-owned section (§1–§14). To *add* a project-specific invariant
instead of changing a forge one, you don't amend at all: you add a `§P`
section to `CONSTITUTION.project.md` (see "Project-specific extensions"
above), which is additive and needs no §11.1 PR.

### The §11.1 process

1. Open a PR that edits **only** `CONSTITUTION.md` (no concurrent code
   changes).
2. PR title: `Constitution: <short rationale>`.
3. PR body answers four questions:
   - What is changing?
   - Why now?
   - What becomes possible?
   - What becomes impossible?
4. `qa-reviewer` plus one human stakeholder must approve.
5. On merge, increment the version and date the entry in the revision log
   at the bottom of `CONSTITUTION.md`.

### When to amend

Common legitimate reasons:

- Your stack actually changed (added Redis, moved off Postgres, picked a
  new HTTP framework).
- A non-negotiable proved too strict for a justified use case (e.g., §2.6
  vendoring — sometimes vendoring is the right call for supply-chain
  isolation).
- Your performance budgets need adjustment because real measurements
  contradicted the initial guess.
- The project's accessibility floor needs to be tightened (or loosened, for
  a backend-only project).

### When not to amend

- "This one feature does not fit the constitution." Then either reshape the
  feature, or amend the rule that prevents it — not both.
- "We need to ship by Friday." Constitution amendments are not the right
  tool for deadline pressure. Manual single-agent invocation
  exist for fast-path work that does not need new gates.
- "This rule annoys me." If a rule is creating friction without preventing
  problems, fine — write the amendment with an honest rationale. But the
  burden of argument is on you, not the rule.

### The revision log

At the bottom of `CONSTITUTION.md`:

```markdown
## Revision log

- **v0.1 (TBD)** — Initial copy from `CONSTITUTION.template.md`. Awaiting
  stack decisions in §1 and budgets in §6.
- **v0.2 (2026-03-12)** — Filled §1 (Node + Fastify + Postgres + Redis +
  Stripe). Filled §6 with 200ms p95 / 800ms p99.
- **v0.3 (2026-05-04)** — Amended §2.6 to allow vendoring for crypto
  dependencies after the upstream-compromise incident. Auditor still
  required.
```

Date every entry. Future-you will want to know when each rule landed.

---

## Conflicts the constitution catches

Examples of what agents will reject upstream because of constitutional
violations.

- **Spec asks for plaintext password storage.** `security-auditor` rejects
  to `spec-architect` citing §5 (cryptography: use platform primitives, no
  hand-rolled crypto, no MD5/SHA1 for auth).
- **Spec asks for a single-phase column drop in a migration.**
  `database-designer` rejects to `spec-architect` citing §2.2 (no
  destructive migrations in a single deploy).
- **Spec asks for a new endpoint with no auth check on a state-changing
  POST.** `security-auditor` rejects citing §2.4 (no unauthenticated
  mutation endpoints).
- **Implementation logs the full request body on a `/login` endpoint.**
  `observability-auditor` rejects to `developer` citing §5 (no PII /
  secrets in logs) and §8.
- **CI workflow does not include the security audit step.**
  `qa-reviewer` rejects to `devops-engineer` citing §9 (Definition of Done
  requires `security-auditor` review).
- **Deploy command exists but no rollback plan is documented.**
  `release-engineer` rejects to `devops-engineer` citing §2.7 (no deploy
  without rollback path) and §9.

In each case, the agent does not work around the violation. It rejects to
the agent that owns the upstream artifact. That agent updates the artifact,
and the pipeline re-runs.

---

## Next step

The constitution is the most consequential file you will fill in. Once §1 is
done, the rest of the pipeline can run.

If you want to know how the permission system that contains the agents
works — including why the constitution itself is protected from agent edits
to §2 / §5 / §8 — read [`customizing.md`](customizing.md).
