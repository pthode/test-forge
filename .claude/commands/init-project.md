---
name: init-project
description: Bootstrap a fresh template clone into a working project. Renames CONSTITUTION.template.md to CONSTITUTION.md (replacing <project> placeholders), removes the template, cleans up forge-internal documentation, writes a project stub README and CONTRIBUTING.md, and updates CLAUDE.md's Product line. Idempotent on a fresh clone; refuses to overwrite a project that has already been bootstrapped.
---

# /init-project — bootstrap this template clone

Argument: `<product-name>` (kebab-case, becomes the product identifier).

If no argument is given, ask the user "What is the product name? (kebab-case)" once, then proceed.

## Steps (execute in order)

1. **Validate the name.**
   - Must match `^[a-z][a-z0-9-]+$` (lowercase, alphanumeric + hyphens, starts with a letter).
   - If validation fails, print the rule that was violated and stop.

2. **Check if the template has already been bootstrapped.**
   - Read `CLAUDE.md`. If the `**Product:**` line still reads `_template — ..._`, the repo is a fresh template clone — proceed.
   - If it already names a product (`**Product:** <existing-name>`), ask the user:

     > This repo is already bootstrapped as `<existing-name>`. Re-running `/init-project` will overwrite `CONSTITUTION.md` and change the Product line. Proceed?

     Wait for an explicit `yes` before continuing. On `no`, stop.

3. **Check that `CONSTITUTION.template.md` exists.**
   - If yes, this is a fresh template — continue to step 4.
   - If no, but `CONSTITUTION.md` already exists, the repo has been bootstrapped before. Ask the user whether to overwrite `CONSTITUTION.md` from a fresh copy of the template (which they must restore from git history first) or to abort. Default: abort.

4. **Create `CONSTITUTION.md` from the template.**
   - Read `CONSTITUTION.template.md`.
   - Write its contents to `CONSTITUTION.md`, with every literal `<project>` replaced by `<product-name>`.
   - Verify the new file exists and contains the product name where the placeholders used to be.

5. **Remove `CONSTITUTION.template.md`.**
   - Delete the template file. It is no longer needed; the filled-in `CONSTITUTION.md` is the canonical record. If the user ever needs to re-bootstrap, they can recover the template from git history.

6. **Clean up forge-internal documentation.**

   Delete the following files from `docs/` — they are agent-forge documentation, irrelevant for the product project:

   - `docs/README.md`
   - `docs/audit-prompt.md`
   - `docs/constitution.md`
   - `docs/customizing.md`
   - `docs/getting-started.md`
   - `docs/how-it-works.md`
   - `docs/task-flows.md`
   - `docs/intent.md`
   - `docs/troubleshooting.md`

   **Do NOT delete `docs/migrations/`** — that directory holds upgrade guides referenced by `UPGRADING.md` and used by `/forge-update`. It must remain.

   If any file in the delete list does not exist, skip it silently — the cleanup is idempotent.

7. **Replace `README.md` with a project stub.**

   The forge's own README is no longer relevant for the bootstrapped project. Overwrite `README.md` at the repo root with this exact content (substituting `<product-name>`):

   ```markdown
   # <product-name>

   This project is under construction. The README will be expanded as features ship.

   For the development workflow, see [CONTRIBUTING.md](CONTRIBUTING.md).
   ```

   `doc-writer` will replace this stub with a real product README on the first feature ship.

8. **Update `CLAUDE.md`'s Product line.**
   - Find the line near the top that reads:

     ```markdown
     **Product:** _template — run `/init-project <product-name>` to bootstrap._
     ```

   - Replace with:

     ```markdown
     **Product:** `<product-name>`
     ```

9. **Verify `.forge-version`.**

   The `.forge-version` file already exists at the repo root (it was there in the clone).
   No action needed — it travels with the repo. Verify it exists and print its contents
   (`cat .forge-version`) so the user can confirm the baseline forge version.

### File-creation policy for steps 10–16

Steps 10–16 write project-owned files. Which files already exist depends on
how you got here, and the right behavior differs:

- **Fresh template clone** (Step 2 found `_template`): write each file
  **unconditionally**, replacing any copy the template shipped. A fresh clone
  of the forge carries the forge's *own* `CLAUDE.project.md` and `BACKLOG.md`
  (and may carry others); overwriting them here is exactly what stops
  forge-internal content from leaking into the product.
- **Confirmed re-run** of an already-bootstrapped project (Step 2 / Step 3
  got an explicit `yes`): do **NOT** clobber files the project has filled in
  or accumulated. Skip `CLAUDE.project.md`, `CONSTITUTION.project.md`,
  `CONTRIBUTING.md`, `BACKLOG.md`, and `CHANGELOG.md` if they already exist
  with project content — refresh only `CONSTITUTION.md` and the `Product:`
  line (the files Step 2's prompt warned about). Wiping a real project's
  backlog or changelog on a re-init is data loss.

10. **Create `CLAUDE.project.md`.** (Per the file-creation policy above:
    overwrite on a fresh clone — the forge ships its own `CLAUDE.project.md`
    with meta-work rules that must not survive into the product; preserve on
    a confirmed re-run.)

    Create a file named `CLAUDE.project.md` at the repo root with this exact content:

    ```markdown
    # Project-specific router instructions

    This file extends `CLAUDE.md` with instructions specific to this project.
    Add custom routing rules, domain anti-patterns, or project invariants here.
    `CLAUDE.md` imports this file automatically at the end — Claude sees both.

    ## Custom routing

    <!-- Add project-specific routing rules here, e.g.:
    - "build me a report" → developer (report generation is a product feature here)
    -->

    ## Project anti-patterns

    <!-- Add project-specific anti-patterns here, beyond those in CLAUDE.md. -->

    ## Additional invariants

    <!-- Add project invariants that don't fit in CONSTITUTION.md but affect how
         the router should behave. For example, domain-specific terminology,
         third-party integration rules, or workflow constraints. -->
    ```

11. **Create `CONSTITUTION.project.md`.**

    Create a file named `CONSTITUTION.project.md` at the repo root with this exact content (substituting `<product-name>`):

    ```markdown
    # <product-name> — Project-specific constitution extensions

    This file extends `CONSTITUTION.md` with invariants that are specific to this project. Per `CONSTITUTION.md §11.2`:

    - Numbering uses the `§P` prefix: `§P1`, `§P2`, `§P3`, … — never numerical, so future forge sections (§15, §16, …) cannot collide.
    - **Additive only.** Project sections must NOT contradict or override any forge section in `CONSTITUTION.md` (§1–§14). If you need to change a forge section, go through §11.1 amendment process.
    - Every agent that reads `CONSTITUTION.md` also reads this file. Project rules are binding in the same way forge rules are.
    - `/forge-update` never touches this file. It is owned by the project team.

    ## How to add a project section

    1. Pick the next sequential `§P<N>`.
    2. Write the section as you would a forge section: title, rationale, bulleted rules.
    3. Mention `§P<N>` in any spec, ticket, or code comment that depends on it.

    <!-- Example:

    ## §P1. Data residency

    All production data MUST remain within the EU. No data crosses to non-EU cloud regions, including for backup, analytics, or DR.

    - All cloud resources are provisioned in `eu-west-1` or `eu-central-1`.
    - Third-party SaaS used in production must be GDPR-compliant AND host data in the EU.
    - `security-auditor` blocks any change that introduces a non-EU dependency.

    -->

    ## Project sections

    <!-- Add §P1, §P2, … below. -->
    ```

    `CONSTITUTION.project.md` is project-owned. The team edits it freely. `/forge-update` never touches it.

12. **Create `CONTRIBUTING.md`.**

    Create a file named `CONTRIBUTING.md` at the repo root with this exact content (substituting `<product-name>`):

    ```markdown
    # Contributing to <product-name>

    This project uses [agent-forge](https://github.com/pthode/agent-forge) for AI-assisted development. All substantial changes flow through a pipeline of specialized agents — defined in `.claude/agents/` — orchestrated by Claude in `CLAUDE.md`.

    ## Common workflows

    - **New feature:** run `/autopilot <description>` and answer the intake questions.
    - **Bug fix or small change:** open Claude and describe the change — it routes to the right agent.
    - **Upgrade the forge scaffold:** run `/forge-update`.

    ## Where things live

    - Pipeline rules and routing table — `CLAUDE.md`
    - Project invariants and non-negotiables — `CONSTITUTION.md`
    - Agent definitions (live source of truth) — `.claude/agents/`
    - Slash commands — `.claude/commands/`
    - Upgrade history — `UPGRADING.md`

    ## Learn more

    Full agent-forge documentation: <https://github.com/pthode/agent-forge>
    ```

    `CONTRIBUTING.md` is project-owned. The team edits it freely as the workflow evolves. `/forge-update` never touches it.

13. **Create `BACKLOG.md`.** (Per the file-creation policy above: overwrite
    on a fresh clone — the forge ships its own `BACKLOG.md` of scaffold
    tech-debt that must not leak into the product; preserve on a confirmed
    re-run so an accumulated project backlog is not wiped.)

    Create a file named `BACKLOG.md` at the repo root with this exact content (substituting `<product-name>`):

    ```markdown
    # <product-name> — Backlog

    Tech debt, deferred fixes, and known cleanup items. Reviewers append entries during the pipeline; the team works through them with `refactor-specialist` or `/autopilot` as capacity allows. See CONSTITUTION.md §12 for the discipline that governs this file.

    ## How this file works

    - **Reviewers write here, not into feature PRs.** Every minor finding from `qa-reviewer`, `code-reviewer`, `security-auditor`, `performance-analyst`, `ux-consultant`, or `observability-auditor` lands here as a numbered entry. Inline minor fixes during a feature PR are forbidden — they bloat scope and drown the diff.
    - **IDs are sequential, never reused.** Use `B-001`, `B-002`, … in order. When you close an entry, move it to "Closed entries" below; do not renumber.
    - **Take an item:** invoke `refactor-specialist B-NNN` for behavior-preserving cleanup, or `/autopilot <description referencing B-NNN>` for items that need full pipeline treatment (schema changes, new contracts, etc.).
    - **Deadlines are real.** When a pipeline run starts and finds an entry past its deadline, the orchestrator promotes that entry to a `major` finding on the current iteration. Don't write deadlines you don't intend to honor.

    ## Active entries

    <!-- Reviewers append entries here. Format per CONSTITUTION.md §12.2. -->

    ## Closed entries (audit trail — one release cycle)

    <!-- Move resolved entries here. Archive entries older than one release cycle. -->
    ```

    `BACKLOG.md` is project-owned. `/forge-update` never touches it.

14. **Ask the three monitoring scope questions.**

    Use `AskUserQuestion` with three yes/no questions (or ask them sequentially if interactive mode doesn't support batching):

    - "Does your project have compliance or legal obligations that require audit trails? (SOC2, HIPAA, GDPR data-access records, financial audit, etc.)"
    - "Does your project need product analytics — tracking how users navigate or use features?"
    - "Does your project need security event monitoring? (anomaly detection, intrusion detection, SIEM)"

    For each answer:
    - **yes** → in `CONSTITUTION.md`, change the matching sub-section's scope marker from `[scope: disabled]` to `[scope: enabled]`. The TBD fields stay TBD — the team fills them when they choose a platform.
    - **no** → leave the marker as `[scope: disabled]`. The concern is declared and documented but skipped by all agents.

    The `[scope: always-on]` marker on §8a is never changed — operational observability is unconditional.

15. **Ask the test strategy questions.**

    Use `AskUserQuestion` with three questions (batch as a single call):

    **Question A — Local isolation strategy** (what infrastructure does the test suite need to run?):
    - "None needed — tests require no external infrastructure (in-memory / SQLite / pure functions)"
    - "In-memory substitutes — replace each service in-process (e.g. pg-mem, fakeredis, localstack)"
    - "Docker Compose — containerized real services running locally alongside the test suite"
    - "CI-only — full integration suite runs only in CI; developers run unit tests locally"

    **Question B — Cloud dev policy** (may tests use live cloud credentials during development?):
    - "No cloud — tests must never require live cloud credentials or call external APIs"
    - "Test accounts only — vendor sandbox / test-mode keys are acceptable in development"
    - "Unrestricted — document any cloud dependencies explicitly in §4.1"

    **Question C — E2E scope** (what must be green before a feature is merged?):
    - "Disabled — unit and integration tests are sufficient; no E2E suite"
    - "Smoke only — smoke tests run in the release CI gate, not per-feature merge"
    - "Critical paths — E2E on core user flows must pass before merge"
    - "Full E2E suite — complete E2E suite must pass before merge"

    **Question D — Coverage floor** (what minimum test coverage % does CI enforce?):
    - "No floor — coverage is tracked but not gated"
    - "50% — minimum reasonable bar for app code"
    - "70% — recommended default for production services"
    - "80% — strict, suitable for libraries / SDKs"

    For each answer, update `CONSTITUTION.md` §4:

    - **§4 `Coverage floor`:** replace `_TBD_` with the chosen value (e.g. `0` for "no floor", `50`, `70`, `80`). If "no floor", change the surrounding sentence to `"Coverage floor: 0 % (tracked but not gated)."`.
    - **§4.1 `Local isolation strategy`:** replace `_TBD_` with the chosen option verbatim.
    - **§4.1 `Cloud dev policy`:** replace `_TBD_` with the chosen option verbatim. If "None needed" was chosen for isolation, default cloud policy to `no-cloud` unless the user chose otherwise.
    - **§4.1 `Services required for tests`:** if isolation is Docker Compose or in-memory substitutes, replace `_TBD_` with `"Fill in each service and its local equivalent, e.g. Postgres: docker-compose; Redis: in-memory."` Otherwise set to `"N/A"`.
    - **§4.2 (TDD policy):** always replace `_TBD_` with `spec-derived-post-impl — test-engineer after developer, tests derived from spec (pipeline default)`. No question needed.
    - **§4.3 (E2E policy):** replace `_TBD_` with the chosen option verbatim.
    - After each section update, change that section's `[scope: TBD]` marker to `[scope: set]`.

16. **Ask the versioning model question.**

    Use `AskUserQuestion` with one question:

    **Question — How will this project be versioned?**
    - "Semver — MAJOR.MINOR.PATCH (recommended for libraries, SDKs, CLIs, anything with external consumers)"
    - "Calver — YYYY.MM.MICRO (recommended for apps, services, internal tools where users want the latest)"
    - "None — no formal versioning; releases tracked by git commit hash (recommended for continuous-deployment services without a consumer-facing API)"
    - "Custom — I'll describe the scheme manually in §13.2 after init"

    For each answer, update `CONSTITUTION.md` §13:

    - **§13.1 `Scheme`:** replace `_TBD_` with `semver` / `calver` / `none` / `custom` matching the choice.
    - **§13.1 `Version field location`:** if §1 stack is known (rare at init time), set to the conventional path for that stack (`package.json:version` for Node, `pyproject.toml:[project].version` for Python, `Cargo.toml:[package].version` for Rust, `go.mod` does not carry a version field — leave as `N/A`). Otherwise leave as `_TBD_` with the inline comment `Fill in once §1 stack is locked.` Set to `N/A` if the scheme is `none`.
    - **§13.2 `What each component means`:** replace `_TBD_` with the appropriate per-scheme block from §13.5 (copy verbatim from the constitution's own reference; do NOT paraphrase). For `custom`, leave as `_TBD: describe the scheme below._` for the user to fill in.
    - Change `[scope: TBD]` to `[scope: set]`.

    **Conditional: create `CHANGELOG.md`.** If the chosen scheme is `semver`, `calver`, or `custom`, create `CHANGELOG.md` at the repo root with this exact content (substituting `<product-name>`):

    ```markdown
    # <product-name> — Changelog

    All notable changes to this project are documented here, following [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) format. Versioning follows the model defined in `CONSTITUTION.md §13`.

    ## [Unreleased]

    ### Added

    <!-- New features, capabilities, or files. doc-writer appends here on each feature ship. -->

    ### Changed

    <!-- Changes in existing functionality. -->

    ### Deprecated

    <!-- Soon-to-be-removed features. -->

    ### Removed

    <!-- Features removed in this release. -->

    ### Fixed

    <!-- Bug fixes. -->

    ### Security

    <!-- Security-related changes; cross-reference /docs/security-reports/. -->
    ```

    If the chosen scheme is `none`, do NOT create `CHANGELOG.md`. The constitution §13 records the decision.

    `CHANGELOG.md` is project-owned. `/forge-update` never touches it.

17. **Ask the workflow-autonomy question.**

    Use `AskUserQuestion` with one question:

    **Question — How autonomous should the orchestrator be with `commit → push → PR → merge`?**
    - "Review all — pause before every commit, PR, and merge (recommended; the safe default, identical to today's behavior)"
    - "Review critical only — autonomous on routine work; pause on critical changes (security-sensitive files, schema migrations, public API contracts, new dependencies)"
    - "Autonomous — drive commit → push → PR → merge within the protected-branch + permission floor; surface only urgent items and security-sensitive confirmations"

    Update `CONSTITUTION.md` §14:

    - **§14.2 `Level`:** replace `_TBD_` with `review-all` / `review-critical` / `autonomous` matching the choice.
    - Change `[scope: TBD]` to `[scope: set]`.

    The §14.1 floor is fixed and is NOT affected by this answer — protected branches stay PR-only, the permission model is never loosened, CI must be green before merge, and security-sensitive changes always get human confirmation regardless of level.

18. **Print the next-step checklist.**

    ```text
    ✓ `<product-name>` bootstrapped.

    Next steps before /autopilot will accept work:
      1. Edit CONSTITUTION.md §1 (Stack & boundaries).
         At minimum, declare: language, framework, datastore.
      2. For each §8 concern you enabled (§8b audit, §8c analytics, §8d security),
         fill in the TBD fields: platform, retention, PII rules.
      3. Review CONSTITUTION.md §4.1 (Test environment). If you chose Docker Compose or
         in-memory substitutes, fill in "Services required for tests" with specifics,
         e.g. "Postgres: docker-compose; Redis: in-memory".
      4. If the project is latency-sensitive, fill §6 (Performance budgets).
      5. Create .claude/settings.local.json with stack-specific narrow allows
         (see CLAUDE.md §"Bootstrapping this template" for the snippet).
      6. Run /autopilot <a description of the first feature>.

    The intake agent will refuse to lock a ticket while §1 stays TBD —
    that's intentional. Fill it in now.
    ```

## Forbidden actions

You MUST NOT:

- Pre-fill any field in `CONSTITUTION.md` §1 with a guess. The whole point of the TBD enforcement is that humans pick the stack.
- Touch `.claude/agents/` or `.claude/commands/` — those are scaffold-level, not project-level.
- Touch `.claude/settings.json` — that file is protected by deny rules and is the user's responsibility.
- Initialize, modify, or commit any git state. The user owns the git workflow; the repo they cloned already has a git history.
- Delete `docs/migrations/` or any file under it — those are upgrade guides referenced by `UPGRADING.md` and used by `/forge-update`.
- Create any directory tree (`src/`, `tests/`, `docs/specs/`, etc.). Those are created by the agents on demand during pipeline runs.

## Failure modes

- **`CONSTITUTION.template.md` missing AND `CONSTITUTION.md` already exists** — the repo has been bootstrapped before. Abort with a clear message; the user can re-run only after restoring the template from git history.
- **`CLAUDE.md` doesn't contain the expected `Product:` line** — print a diagnostic and ask the user to update CLAUDE.md manually, then re-run.
- **Name validation fails** — print the violated rule and stop. Nothing is created.
- **Filesystem error while writing `CONSTITUTION.md`** — leave the template untouched, report the error, exit. Idempotent retry must be safe.
