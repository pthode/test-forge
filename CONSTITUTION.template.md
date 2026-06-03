# <project> — Constitution

> **Template.** Run `/init-project <product-name>` in Claude Code from the repository root: it renames this file to `CONSTITUTION.md`, replaces every `<project>` placeholder with your product name, and removes the template. Then fill in §1 (Stack) and §6 (Performance budgets) before the first `/autopilot` run. The intake agent will refuse to lock a ticket while load-bearing sections remain `TBD`.

This document defines the **project-level invariants** that every agent must respect when producing specs, code, tests, docs, or reviews. The constitution is load-bearing: a spec, implementation, or PR that contradicts it is rejected, regardless of how well it satisfies the immediate task.

> **Precedence:** Constitution > Spec > Implementation > Tests > Docs.
> If the spec contradicts the constitution, the spec must change first (route to `spec-architect` with a REJECT citing the constitution).

---

## 1. Stack & boundaries

> **Fill these in before the first `/autopilot` run.** Until filled, `spec-architect` MUST emit an `URGENT: yes` CLARIFY rather than guessing.

- **Language(s) & runtime:** _TBD_
- **Framework(s):** _TBD_
- **Datastore(s):** _TBD_
- **External services we depend on:** _TBD_
- **Deployment target:** _TBD_
- **Supported clients / browsers / OSs:** _TBD_

---

## 2. Non-negotiables

These are the rules that override convenience. Breaking one requires an explicit constitutional amendment (see §11), not a one-off exception.

1. **No secrets in code or images.** Secrets come from the runtime environment. `.env.example` documents shape only, never values.
2. **No destructive migrations in a single deploy.** Schema changes are two-phase: add → backfill → flip writes → remove (separate releases).
3. **No silent data loss.** Any code path that drops, truncates, or coerces user data must log + surface the loss.
4. **No unauthenticated mutation endpoints.** Every write requires an authenticated principal; authorization is checked at the handler, not the client.
5. **No `// TODO` left in `main`.** Tracked work goes in the issue tracker; transient notes go in the PR body and are removed before merge.
6. **No vendored copies of third-party code** unless the dependency-auditor has signed off in `/docs/dependency-reports/`.
7. **No deploy without an observability footprint** (§8) and a rollback path (§9 DoD).

---

## 3. Code style anchors

- **Naming:** prefer full words over abbreviations (`userRepository`, not `usrRepo`). Acronyms ≤3 letters stay uppercase (`URL`, `ID`); longer acronyms become PascalCase (`Http`, not `HTTP`).
- **Functions:** one purpose per function. If you need "and" to describe what it does, split it.
- **Comments:** explain *why*, never *what*. Code that needs *what*-comments is code that needs renaming.
- **Errors:** raise/return errors at the boundary they originate from; do not catch-and-swallow. Wrap with context when re-raising across layers.
- **Imports:** absolute imports from the project root, not relative chains (`../../../`).
- **Formatting:** whatever the project formatter says — never hand-format. CI fails on unformatted code.

---

## 4. Test discipline

- **Spec is the source of truth for tests**, not the implementation. If a test passes against buggy code, the test is also wrong.
- **Test pyramid:** more unit than integration, more integration than e2e. If you reach for e2e first, reconsider.
- **No mocks of code you own.** Mock external boundaries (HTTP, time, filesystem, third-party SDKs); use the real thing for internal modules.
- **No mocks of the database in integration tests.** Use a real database (containerized or in-memory equivalent that matches the production engine's behavior).
- **Flaky tests are bugs.** A skipped/quarantined test must have a dated issue link and a removal deadline.
- **Coverage floor:** _TBD_ %. Coverage is a smoke alarm, not a goal — 100% coverage of trivial getters proves nothing.

### 4.1 Test environment contract
<!-- Filled in by /init-project -->
- **Local isolation strategy:** _TBD_
- **Services required for tests:** _TBD_
- **Cloud dev policy:** _TBD_

[scope: TBD]

### 4.2 TDD policy
<!-- Filled in by /init-project -->
- _TBD_

[scope: TBD]

### 4.3 E2E policy
<!-- Filled in by /init-project -->
- _TBD_

[scope: TBD]

---

## 5. Security posture

- **Input is hostile by default.** Validate at the boundary; sanitize at the sink (e.g., parameterize SQL, escape HTML in templates, never `eval`).
- **Authn ≠ authz.** Knowing *who* is calling does not tell you *what* they may do. Check both, separately.
- **Least privilege everywhere:** DB roles, API keys, IAM, file permissions. A leaked credential should compromise as little as possible.
- **Cryptography:** use the platform's vetted primitives. No hand-rolled crypto, no MD5/SHA-1 for anything security-sensitive, no ECB.
- **Dependencies:** new direct dependencies require `dependency-auditor` sign-off. Transitive bumps are tracked but not gated.
- **Logging:** never log secrets, tokens, full PII, or full request bodies on auth endpoints. (Observability rules in §8 still apply — log the *event*, redact the *contents*.)

---

## 6. Performance budgets

> **Fill these in before the first `/autopilot` run** on any latency-sensitive feature. Until filled, `performance-analyst` will treat budgets as unset and limit itself to detecting structural issues (N+1 queries, unbounded loops).

- **p95 request latency:** _TBD_ ms
- **p99 request latency:** _TBD_ ms
- **Cold-start budget:** _TBD_ ms
- **Memory ceiling per instance:** _TBD_ MB
- **DB queries per request (steady state):** ≤ _TBD_ — `performance-analyst` REJECTs N+1 patterns regardless of measured timing.

Budgets are checked by `performance-analyst` on any change that touches a hot path, query, loop, or async boundary.

---

## 7. Accessibility & UX baseline (frontend only)

> **Guiding principle:** Build from the edge in. Design every UI surface for the user who needs the most support — keyboard-only navigation, high contrast, screen reader, switch access — and the result works better for every user. Accessibility is not a retrofit; it is a first-class constraint from the first commit.

### 7.1 Standard

- **Conformance target: WCAG 2.2 Level `<wcag_level>`** (default: **AA**). No new component ships below this level. Projects with a public-service or accessibility-first mandate may raise this to AAA by amending this placeholder.
- A failing automated check is a CI blocker, not a warning.
- `<wcag_level>` is locked by `requirements-intake` during the first intake round and referenced by `spec-architect` for every UI feature.

### 7.2 Scope

The following surfaces are in scope for accessibility conformance:

- `<ui_surfaces>` — _TBD: replace with the list of UI surfaces this project exposes (e.g., "web app at `/`, admin dashboard at `/admin`, public marketing pages")._

All surfaces listed here are subject to §7.3 automated gating and §7.4 manual review. Surfaces added after initial bootstrap require a constitution amendment (§11) to be brought into scope.

### 7.3 Automated gate

- **Test integration:** use the axe-core–based adapter that matches the §1 stack — `jest-axe` for Jest/React, `vitest-axe` for Vitest, `playwright-axe` for Playwright e2e. Adapter choice follows from the stack declared in §1; if the right adapter is ambiguous, `requirements-intake` asks before locking the ticket.
- **Zero violations** reported by the chosen adapter is a **CI hard gate** — the build fails on any reported violation. Suppressions require a dated inline comment and a linked issue with a remediation deadline.
- Automated checks catch roughly 30–40% of WCAG issues. They are a necessary floor, not a ceiling. Manual review (§7.4) covers the remainder.

### 7.4 Manual review

- **`ux-consultant` review is mandatory** for every UI change before merge, regardless of component size or perceived triviality.
- `ux-consultant` validates against the AT matrix in §7.7. A change that passes automated checks but fails manual AT review is a **blocker**.

### 7.5 Baseline UX requirements

Every interactive surface MUST:

- Be **keyboard-first:** all interactive elements reachable and operable without a pointing device; tab order matches visual reading order; focus indicator is always visible and meets 3:1 contrast ratio.
- Use **no color-only signaling:** error, success, focus, warning, and status states are conveyed by shape, icon, label, or pattern — never by color alone.
- Render **loading, empty, and error states** as first-class UI states with appropriate ARIA live regions; a component without all three is incomplete.
- **Announce form errors** inline next to the originating field using `aria-describedby` or equivalent, surviving re-validation without losing focus context.

### 7.6 Third-party component policy

When a required third-party component fails the §7.1 conformance target, apply this three-step escalation in order — do not skip steps:

1. **Find an alternative** that meets conformance. Prefer a component that ships with correct ARIA roles and keyboard interaction patterns built in.
2. **Patch or wrap** the chosen component to close specific gaps. Document the patch in the PR and track the upstream issue.
3. **Document a time-boxed exception** in `/docs/ux-reviews/a11y-exceptions.md`: component name, specific failure, remediation plan, and expiry date. `ux-consultant` must sign off. `qa-reviewer` will not accept undocumented exceptions.

### 7.7 Target AT matrix

`ux-consultant` manual review covers, at minimum:

| Assistive Technology | Browser | Platform | Notes |
| --- | --- | --- | --- |
| NVDA (latest) | Firefox (latest) | Windows | Primary SR baseline for desktop |
| VoiceOver (latest) | Safari (latest) | macOS + iOS | Required for Apple ecosystem |
| TalkBack (latest) | Chrome (latest) | Android | Required if any mobile-web surface is in scope |

Projects may add rows (e.g., JAWS for enterprise deployments) or drop the TalkBack row if no mobile surface is in scope — amend this table via §11. Do not remove the NVDA or VoiceOver rows; they cover the two largest screen-reader user populations.

---

## 8. Monitoring & observability

Monitoring covers four distinct concerns with different consumers, retention requirements, and legal obligations. Each concern is declared below with a **scope marker**. Flipping a marker from `disabled` to `enabled` and filling in the TBD fields is a two-line CONSTITUTION change — purely additive, no pipeline restructuring needed.

---

### 8a. Operational observability `[scope: always-on]`

This concern is **never opt-out**. The rules below apply to every production deployment regardless of stack or feature size.

This section is about **structured event logging discipline**, not event-driven architecture. The architecture (synchronous request/response, pub/sub, event sourcing, etc.) is a §1 stack decision. The rules below apply regardless of which architecture you picked.

- **Every business-meaningful state change emits one structured log line.** The schema is `{ts, level, event, actor_id, resource_id, ...domain_fields, trace_id}`. "Business-meaningful" means: anything an auditor, a support engineer, or a product manager would want to reconstruct after the fact. User signed up, order placed, payment failed, permission granted/revoked.
- **Log lines are machine-parseable** (JSON or your platform's structured-log format). No `printf` debugging in production paths.
- **Stable event names.** Event names live in a code-level enum/const, not as inline strings, so renaming them is a typed refactor and the analytics/alerting side stays in sync.
- **No PII or secrets in log payloads.** Reference resources by stable ID; redact email, name, address, tokens, full request bodies. (Reinforced by §5.)
- **Correlation IDs propagate across services.** Every inbound request creates or extracts a `trace_id`; every outbound call carries it. Every log line in the request's path includes it.
- **Log levels are calibrated:**
  - `ERROR` — the request failed in a way the caller needs to know about; an oncall human should see this if it spikes.
  - `WARN` — degraded behavior, recoverable, but worth tracking.
  - `INFO` — significant business events (the §8a staple).
  - `DEBUG` — disabled in production by default.
- **Every spec-mandated success criterion and every spec-mandated failure mode has a corresponding logged event.** `observability-auditor` enforces this mapping.
- **Metrics complement, never replace, structured events.** A counter that `order_placed` happened is fine; it does not replace the structured log line that carries the order ID.
- **Alerts have runbooks.** If you fire a page, the alert links to a runbook explaining what to do. Alerts without runbooks are noise.

> Event-driven *architecture* (pub/sub, event bus, event sourcing) is a stack choice, not a constitutional mandate. Do not adopt it for projects where it adds complexity without clear payoff. Structured event *logging* (above) is mandatory regardless.

**Agent responsibilities when scope: always-on:**
`spec-architect` enumerates required events in spec §10 (Observability plan). `developer` implements them from code-level enum/const. `devops-engineer` registers alert rules and runbooks. `observability-auditor` verifies event coverage in Phase 3. `release-engineer` Gate 5 confirms events are live in the target environment.

---

### 8b. Audit logging `[scope: disabled]`

Immutable, append-only record of privileged actions for compliance, legal, and accountability purposes.

- **Retention:** TBD.
- **Platform:** TBD (append-only database table | CloudTrail | dedicated audit service).
- **Trigger events:** admin action, permission grant/revoke, data export, login/logout, record deletion.
- **Required fields:** `{ts, actor_id, action, resource_type, resource_id, ip, user_agent, result}`.
- **Immutability guarantee:** TBD (append-only table with no UPDATE/DELETE | WAL-level | external immutable store).

> Audit logs are a separate concern from operational logs. They answer "who did what, when, to which resource?" for human accountability — not "what broke and why?" for system debugging. Never route audit events only to an operational log aggregator where they can be overwritten or expired.

**Agent responsibilities when scope: enabled:**
`spec-architect` must enumerate audit events in spec §10. `database-designer` creates the audit table (with append-only constraint). `developer` writes to it. `observability-auditor` verifies audit event coverage. `security-auditor` verifies immutability and access controls on the audit store.

---

### 8c. Product analytics `[scope: disabled]`

User behaviour and feature usage tracking for product insight, funnels, and experimentation.

- **Platform:** TBD (PostHog | Mixpanel | Amplitude | Segment | custom).
- **PII rules:** TBD (anonymous IDs only | pseudonymised | explicit consent required before first event).
- **Client-side / server-side split:** TBD.
- **Event ownership:** product/analytics team defines the event taxonomy; engineering implements.

> Product analytics events are not operational logs. They answer "how are users using the app?" — not "did the system behave correctly?" Do not conflate them: operational logs should not be exported wholesale to analytics platforms (PII risk), and analytics events should not substitute for operational coverage.

**Agent responsibilities when scope: enabled:**
`spec-architect` enumerates analytics events in spec §10. `developer` instruments them using the chosen platform's SDK. `observability-auditor` verifies analytics events fire in staging. `ux-consultant` advises on event granularity for UX flows.

---

### 8d. Security event monitoring `[scope: disabled]`

Anomaly detection and threat visibility for SecOps and incident response.

- **Platform:** TBD (Wazuh | Falco | GuardDuty | Datadog Security | SIEM of choice).
- **Trigger events:** failed-auth spike, impossible travel, privilege escalation, unusual data-volume export, scanner/fuzzer signatures.
- **Alert escalation path:** TBD (PagerDuty | Slack | email | ticketing system).
- **Retention:** TBD (often 1 year minimum for compliance).

> Security monitoring events overlap with operational logs (failed logins appear in both) but have a different consumer (SecOps, not on-call engineering) and different retention. Do not rely on the operational log pipeline to satisfy security monitoring obligations — route to the designated SIEM separately.

**Agent responsibilities when scope: enabled:**
`security-auditor` includes security-event coverage checks in every audit. `devops-engineer` provisions detection rules and alert routing. `observability-auditor` spot-checks that trigger events fire in staging and are reaching the SIEM.

---

## 9. Definition of Done

A change is **Done** only when **all** of the following hold:

- [ ] Spec exists under `/docs/specs/` and matches the implementation.
- [ ] Implementation compiles / type-checks / lints clean.
- [ ] Tests added or updated; full suite green locally **and in CI**.
- [ ] Docs (`README`, API docs, `CHANGELOG`) reflect the change.
- [ ] Migrations (if any) are reversible and two-phase.
- [ ] `security-auditor` reviewed (or explicitly waived as non-applicable in writing).
- [ ] `observability-auditor` confirms each spec event/failure-mode has a logged counterpart.
- [ ] Monitoring / alert rules updated for new endpoints or workers (owned by `release-engineer`).
- [ ] **Rollback path documented** — exact steps to revert if the deploy goes wrong (in the release report).
- [ ] `qa-reviewer` accepted.
- [ ] No `blocker` or `major` items open against the change.

"Works on my machine" is not Done. "Deployed but not observable" is not Done.

---

## 10. Branching, commits, and PR hygiene

- **Branch from `main`**, never from another feature branch.
- **One concern per PR.** Refactor + feature in the same PR is two PRs.
- **Commit messages:** imperative mood, ≤72-char subject, body explains *why* (not *what*).
- **No force-push to shared branches.** Force-push only to your own un-reviewed branch.
- **PRs require a green CI** and at least one approving review before merge.

---

## 11. Amendment process

### 11.1 Amending forge-owned sections (§1–§14)

This document is amended, not overridden.

1. Open a PR that edits this file and **only this file** (no concurrent code changes).
2. Title: `Constitution: <short rationale>`.
3. Body must answer: *what is changing, why now, what becomes possible, what becomes impossible.*
4. `qa-reviewer` plus one human stakeholder must approve.
5. On merge, increment the version below and date the entry.

### 11.2 Project-specific extensions (`CONSTITUTION.project.md`)

Numerical sections §1–§14 in this file are forge-owned. As forge evolves it MAY add §15, §16, … in future versions — projects must not occupy that numerical range.

A project that needs its own invariants beyond what forge provides uses a separate file:

- **Location:** `CONSTITUTION.project.md` at the repo root.
- **Numbering:** `§P1`, `§P2`, `§P3`, … — the `P` prefix permanently isolates project sections from forge's numerical range.
- **Created by:** `/init-project` (as an empty stub with the convention documented inline).
- **Owned by:** the project team.
- **Touched by `/forge-update`:** never.

#### Hard rules for `CONSTITUTION.project.md`

- **Additive only.** A project section may add a stricter or additional rule. It may NOT contradict or override any §1–§14 forge section. To change a forge section, use §11.1.
- **Cited by `§P` prefix in agent reports and PRs.** Agents distinguish "forge violated §4" from "project violated §P2" so the owner of each rule is clear.
- **Read by every agent that reads `/CONSTITUTION.md`.** When this file is read, the agent MUST also read `/CONSTITUTION.project.md` if it exists. The forge file is the base; the project file extends it.
- **Override attempt = qa-reviewer blocker.** If `CONSTITUTION.project.md` is written in a way that contradicts §1–§14, `qa-reviewer` treats it as a `blocker` and routes a REJECT back to the project team to fix via §11.1 amendment (or remove the contradicting project section).

---

## 12. Backlog discipline

The pipeline defaults to **fix-now**, not "we'll get to it." Findings that surface during review have exactly three landing places — never a fourth called "we'll remember":

### 12.1 Severity → action mapping (binding)

| Severity | Action | Inline-fix allowed? |
| --- | --- | --- |
| `blocker` | Fix before convergence closes. No exceptions. | Required. |
| `major` | Fix before convergence closes by default. May defer to backlog ONLY with an explicit user decision and a written reason. | Allowed. |
| `minor` | Always logged to `BACKLOG.md`. Never an inline fix in the same iteration. | **Forbidden.** |

Reviewer-internal severity names (`nit`, `nice-to-have`, `LOW`, etc.) all map to canonical `minor` and therefore ALL go to `BACKLOG.md`. There is no "discard unless pattern" carve-out at filing time — that observation can only be made across sessions, and singletons that look trivial in isolation are exactly the inputs that pattern detection needs. Pattern detection happens during grooming (§12.3), not filing.

This stratification forces severity discipline on reviewers: they cannot smuggle "should really be done now" requirements through as `minor`. If a reviewer wants something fixed this iteration, they must classify it as `major` or `blocker` and own that severity call.

### 12.2 `BACKLOG.md` location and format

A single `BACKLOG.md` lives at the repo root. It is project-owned (never touched by `/forge-update`). Each entry uses this structure:

```markdown
## B-NNN — <one-line title>

- **Created:** YYYY-MM-DD
- **Source:** <reviewer-agent> finding during feature `<feature-slug>` iteration <n>
- **Type:** refactor | cleanup | tech-debt | docs | test-gap | observability-gap | other
- **Severity:** minor (singleton) | major (pattern, consolidated from B-X, B-Y, B-Z)
- **Suggested fix:** <one paragraph or pointer to file:line and target pattern>
- **Deadline:** YYYY-MM-DD (default: 90 days from Created)
```

IDs are sequential (`B-001`, `B-002`, …) and never reused. Closed entries move to a "Closed entries" section below the active list and stay for one release cycle as audit trail before archival.

### 12.3 Burndown and grooming

The backlog is a working artifact, not a graveyard. Four mechanisms keep it alive:

1. **`refactor-specialist` accepts a backlog ID as input.** Invoke it as "tackle B-007" and it reads the entry, executes the change in a behavior-preserving way, closes the entry, and commits.
2. **Pattern items earn pipeline runs.** A backlog item promoted to `major` (via grooming) or that requires schema/contract changes routes through `/autopilot <description>` rather than `refactor-specialist`.
3. **`backlog-curator` proposes promotions and archivals.** This agent reads `BACKLOG.md`, finds entries with similar `Type` and `Suggested fix` keywords, and proposes:
   - **Minor → major consolidation** when ≥3 active entries describe the same pattern. The proposal merges them into ONE major entry; on user approval, originals move to "Closed (consolidated into B-NNN)".
   - **Stale singleton archival** when an active minor entry is older than 6 months with no progress.
   - **Systemic warning** when one `Type` exceeds 30% of active entries — surface to the user with a recommendation.
   The curator does NOT execute; it produces `/docs/backlog-reviews/<YYYY-MM-DD>.md`. The user approves, and `refactor-specialist` or the orchestrator applies.
4. **Deadline enforcement.** When a pipeline run starts, the orchestrator scans `BACKLOG.md` for items past their deadline; expired items raise as `major` findings on the current iteration. This prevents indefinite deferral.

### 12.4 Convergence-loop closure

Phase 3 (convergence) closes when:

- Zero `blocker` REJECTs remain, AND
- Zero `major` REJECTs remain (unless explicitly user-deferred to backlog with reason), AND
- All `minor` findings from this iteration have been written to `BACKLOG.md`.

The presence of new `BACKLOG.md` entries from the iteration does NOT prevent closure. The orchestrator writes them in one atomic step after parallel reviewers complete.

### 12.5 Tech-debt visibility

Any pipeline run that adds ≥5 new backlog entries in one iteration MUST surface a warning in the release report: the feature is shipping with a tech-debt tail and the user should consider whether to schedule burndown before the next feature. Similarly, any `backlog-curator` review that flags a systemic warning (one `Type` >30%) surfaces to the user on completion of the curator run.

---

## 13. Release & versioning

<!-- Filled in by /init-project. -->

### 13.1 Versioning model

- **Scheme:** _TBD_ — one of `semver` / `calver` / `none` / `custom`. Defines how releases are numbered and what each version-component means.
- **Version field location:** _TBD_ — path to the canonical version field in the stack's primary manifest (e.g. `package.json:version`, `pyproject.toml:[project].version`, `Cargo.toml:[package].version`). Set to `N/A` if the scheme is `none`.

[scope: TBD]

### 13.2 What each component means

<!-- Filled in by /init-project from the chosen scheme. See the per-scheme reference below. -->

_TBD_

### 13.3 Changelog discipline

- `CHANGELOG.md` lives at the repo root and follows [Keep a Changelog](https://keepachangelog.com) format. Categories: `Added`, `Changed`, `Deprecated`, `Removed`, `Fixed`, `Security`.
- `doc-writer` appends every feature's user-visible changes to the `## [Unreleased]` section under the appropriate category. One bullet per change.
- `release-engineer` renames `Unreleased` to `[<new-version>] — YYYY-MM-DD` on tag, opens a fresh empty `Unreleased` at the top.
- If the scheme is `none`, `CHANGELOG.md` is NOT maintained — the git log is the history. `doc-writer` and `release-engineer` skip CHANGELOG operations.

### 13.4 Release process

- `release-engineer` (Gate 1) reads §13.1 and applies the scheme:
  - `semver` / `calver` / `custom` → bumps the version field at §13.1's path, edits CHANGELOG.md per §13.3, creates immutable git tag `v<new-version>` on merge.
  - `none` → skips all version operations; just opens the PR with branch hygiene as today.
- Tags are immutable. Pre-release tags (`v1.2.0-rc.1` or `v2026.06.1-beta`) are permitted; they do NOT close the `Unreleased` section.

### 13.5 Per-scheme reference (for `init-project`)

When `init-project` writes §13.2 based on the chosen scheme, it uses these canonical descriptions:

#### Semver (`MAJOR.MINOR.PATCH`)

- MAJOR — breaking change to the public API. Existing consumers must update their code to keep working.
- MINOR — new backwards-compatible capability. Consumers benefit but are not forced to change.
- PATCH — bug fix or backwards-compatible correction. No new capability; behavior conforms more closely to the spec.

#### Calver (`YYYY.MM.MICRO`)

- `YYYY.MM` — year and two-digit month of release. Always two digits for month (e.g. `2026.06`, not `2026.6`).
- MICRO — sequential release counter within that month, starting at `1` (e.g. `2026.06.1`, `2026.06.2`).
- No semantic compatibility implication. Calver communicates _when_, not _what changed_.

#### None

- This project does not number releases. Deployments are tracked by git commit hash. `CHANGELOG.md` is not maintained. Re-enabling versioning requires a §11 amendment.

#### Custom

- Describe the scheme in §13.2 manually. `release-engineer` will surface a CLARIFY on first run requesting clarification of bump rules.

---

## 14. Workflow autonomy

How much of the `commit → push → PR → merge` path the orchestrator drives on its own versus pausing for human review. Layered like the permission model: a fixed floor that no setting can lower, plus a configurable level on top.

### 14.1 The floor (never lowered by any autonomy level)

These hold regardless of the level in §14.2 or any personal override:

- `main`, `master`, and `release/*` are PR-only and protected. No agent pushes to them directly, ever (see CLAUDE.md "Branch push model" and the server-side branch protection).
- The permission model (`.claude/settings.json`) is the security boundary. Autonomy never broad-allows interpreters / package managers and never bypasses a `deny` rule.
- Green CI is required before any merge (§10).
- **Security-sensitive changes** — `.claude/settings.json`, this constitution's §2 / §5 / §8, hooks, `Dockerfile` / `.env.example`, MCP / plugin / marketplace additions — ALWAYS require explicit human confirmation, even at `autonomous`. See CLAUDE.md "Security-sensitive changes".
- An `URGENT: yes` CLARIFY always surfaces to the user.

### 14.2 Autonomy level

- **Level:** _TBD_ — one of `review-all` / `review-critical` / `autonomous`. Set by `/init-project`.

[scope: TBD]

The default for new projects is `review-all` — identical to having no autonomy setting at all: nothing lands without a human `ok`. Raise it deliberately.

### 14.3 What each level gates

| Level | The orchestrator pauses for human review before… |
| --- | --- |
| `review-all` | every commit, PR creation, and merge |
| `review-critical` | only **critical** changes (§14.4); routine commits / PRs / merges proceed autonomously |
| `autonomous` | nothing beyond the §14.1 floor — it drives `commit → push → PR → merge` itself, surfacing only `URGENT` and floor-mandated confirmations |

The level governs whether the orchestrator **pauses** — never what is permitted (that is the floor). No level can authorize a direct push to a protected branch or a permission-model bypass.

### 14.4 What counts as "critical"

For `review-critical`, a change is critical if it touches any of:

- the security-sensitive set in §14.1 (settings, §2 / §5 / §8, hooks, `Dockerfile` / `.env`, MCP / plugins),
- a schema migration (`/migrations/`),
- a public API contract (`/docs/api/*.openapi.yaml` or an equivalent published interface),
- a new direct dependency.

Everything else is routine.

### 14.5 Personal override (per-machine)

An individual contributor may set a personal autonomy preference that is **stricter** (more review) than the project level — never looser. It lives per-machine (a `feedback` memory, or a documented personal note), never in the shared repo. The orchestrator uses the **stricter** of (project §14.2 level, personal preference) as the effective level. A personal preference that is *more* autonomous than the project level is ignored.

---

## Revision log

- **v0.1 (TBD)** — Initial copy from `CONSTITUTION.template.md`. Awaiting stack decisions in §1 and budgets in §6.
