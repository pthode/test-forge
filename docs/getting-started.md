# Getting started

> **What this covers:** everything from obtaining the scaffold to running your
> first feature. Three install methods (GitHub template, fork, plain clone),
> the one-time per-machine setup, and two bootstrap paths — fresh template
> clone or importing an existing repository.
>
> **When to read it:** before your first use, on a new machine, or when
> onboarding a teammate.

The scaffold is distributed as a **GitHub template repository**. When you
clone it, the clone IS your product repo. Scaffold files (`CLAUDE.md`,
`.claude/`, `CONSTITUTION.template.md`, `docs/`) live at the repository
root alongside the product code you grow over time. One repo, one git
history, one `.gitignore`.

This is the flat layout. It matches how every other template repository on
GitHub works.

---

## Prerequisites

- [Claude Code](https://claude.com/claude-code) installed and authenticated.
- Git (any recent version).
- A code editor. The scaffold is tested with VS Code on Windows; the agent
  definitions work on any platform Claude Code supports.
- `gh` (GitHub CLI), if you want the release-engineer agent to create PRs
  automatically. Optional for everything else.

---

## Step 1 — Obtain the scaffold

Pick one of three methods.

### Method A — GitHub template (recommended)

Use this if the scaffold lives in a GitHub repository with the "Template
repository" switch flipped on.

1. Visit the scaffold's GitHub page.
2. Click **Use this template** → **Create a new repository**.
3. Pick a name for your **product** — this is your repo name and product
   identity. Pick the owner.
4. `git clone` your new repository to your machine.

The clone IS your product repo. No separate "scaffold repo" exists locally;
scaffold files come with the clone. You start with one clean initial
commit; the scaffold's commit history is not yours to carry forward.

### Method B — Fork

Use this if you intend to **contribute scaffold improvements upstream**.

1. Click **Fork** on the scaffold's GitHub page.
2. `git clone` your fork.
3. `git remote add upstream <original-repo-url>` so you can pull scaffold
   improvements over time.

Trade-off: your fork's git history is the scaffold's. Product work
accumulates on top of it. If you do not plan to contribute back, Method A
is cleaner.

### Method C — Plain clone or download

Use this if you do not have GitHub access (the scaffold is hosted on
GitLab, Gitea, or distributed as a tarball).

1. `git clone <url> <product-name>` (or extract a tarball to
   `<product-name>/`).
2. `cd <product-name>`.
3. Optional: remove `.git/` and `git init` afresh for a clean history.

---

## Step 2 — Verify the scaffold's structure

From the repository root:

```
ls
```

You should see:

```
.claude/
.gitignore
CLAUDE.md
CONSTITUTION.template.md
README.md
docs/
```

If anything is missing, the clone is incomplete; re-clone.

---

## Step 3 — Bootstrap

You have two paths from here, depending on whether you're starting fresh or
bringing an existing project in.

### Path 1 — Fresh template clone (most common)

Open the repo in Claude Code, then run:

```
/init-project <product-name>
```

`<product-name>` is your product in kebab-case (lowercase, alphanumeric +
hyphens, must start with a letter). The command:

1. Validates the name.
2. Reads `CONSTITUTION.template.md`, writes its contents to
   `CONSTITUTION.md` with every `<project>` placeholder replaced by your
   product name.
3. Removes `CONSTITUTION.template.md` (no longer needed; recoverable from
   git history if you ever want to re-bootstrap).
4. Updates the `Product:` line in `CLAUDE.md` from `_template — ...` to
   `<product-name>`.
5. Prints a next-step checklist.

The command takes a few seconds. After it finishes, your repo is no longer
a template — it is your product.

**What `/init-project` does NOT do** (by design):

- Create any directory tree (`src/`, `tests/`, `docs/specs/`, etc.) —
  those are created by agents on demand during the first pipeline run.
- Modify `README.md` — the scaffold welcome stays put until `doc-writer`
  replaces it on first feature ship.
- Touch git state — you commit the bootstrap changes when ready.
- Pre-fill any field in `CONSTITUTION.md` §1 — the `_TBD_` enforcement is
  deliberate; humans pick the stack.
- Create `.claude/settings.local.json` — workspace `settings.json` denies
  agents from writing it, on purpose. You create it by hand in Step 4.

### Path 2 — Existing repository merge

Use this when you already have a product repo and want to apply the
scaffold to it. The flow involves merging scaffold files into your repo
(or merging your repo into a fresh template clone).

**Pick a direction:**

- **A. Pull scaffold files into your existing repo (recommended).** Your
  existing history is preserved entirely. The scaffold lands as one
  discrete commit.
- **B. Use the template, then merge your project in.** Start with a fresh
  template clone and merge your existing code into it. Cleaner initial
  commit history; loses your existing branches and remote config unless
  you re-add them.

The rest of this section covers direction A.

**Steps:**

1. **Inventory conflicts.** The scaffold's files are listed in Step 2.
   Check your existing repo for any of those paths. Common conflicts:
   `README.md`, `.gitignore`, possibly `docs/` if you have one.

2. **Decide how to handle conflicts:**

   - `README.md`: keep the existing one and back up the scaffold's as
     `docs/SCAFFOLD-README.md`, OR replace yours (the scaffold welcome
     is a temporary landing that `doc-writer` will replace on first
     feature ship anyway), OR merge by hand.
   - `.gitignore`: append the scaffold's entries to yours; deduplicate.
   - `docs/`: scaffold docs (`README.md`, `intent.md`, `getting-started.md`,
     `how-it-works.md`, `constitution.md`, `customizing.md`,
     `troubleshooting.md`) coexist with product docs (`docs/specs/`,
     `docs/qa-reports/`, etc.). If your existing `docs/` has files
     matching scaffold names, rename or merge them.
   - `CLAUDE.md`: replace with the scaffold's. Prior agent instructions
     are superseded by the structured pipeline.

3. **Copy the scaffold files in.** If you have the scaffold cloned
   elsewhere:

   ```
   cp -r /path/to/scaffold/.claude .
   cp /path/to/scaffold/CLAUDE.md .
   cp /path/to/scaffold/CONSTITUTION.template.md .
   cp -r /path/to/scaffold/docs/* docs/
   cp /path/to/scaffold/README.md ./README.scaffold.md
   ```

   Or pull from the upstream template URL:

   ```
   git remote add scaffold <scaffold-url>
   git fetch scaffold
   git checkout scaffold/main -- .claude CLAUDE.md CONSTITUTION.template.md docs README.md
   git remote remove scaffold
   ```

4. **Resolve conflicts and stage:** apply your chosen resolutions, then
   `git add` everything you want to track.

5. **Commit:**

   ```
   git commit -m "Adopt agent-forge scaffold"
   ```

6. **Bootstrap with `/init-project <product-name>`** as in Path 1. Use
   your existing product's name (usually the repo name).

7. **Fill `CONSTITUTION.md` §1 from what already exists.** This is an
   existing repo — the stack is already decided. Read your `package.json`
   / `pyproject.toml` / `Cargo.toml` / `Dockerfile` and encode the actual
   answer in §1. See Step 5 below.

---

## Step 4 — Create `.claude/settings.local.json` by hand

This is the most important step and the one most often skipped.

The workspace `.claude/settings.json` is **project-agnostic**. It does not
auto-allow test, build, or lint commands like `pytest`, `npm test`,
`cargo test`, because your stack is unknown at scaffold time. Without
those allows, every test run from the test engineer or QA reviewer
triggers a permission prompt.

Worse: `settings.json` includes a deny rule on agents writing
`.claude/settings.local.json`, on purpose. The agents cannot create this
file for you. You must create it by hand.

Create the file at `.claude/settings.local.json` with a JSON object,
adjusted for your stack:

```json
{
  "permissions": {
    "allow": [
      "Bash(npm test *)",
      "Bash(npm run *)",
      "Bash(npm install)",
      "Bash(npm ci)",
      "Bash(npx tsc *)",
      "Bash(pytest *)",
      "Bash(pip install -r *)",
      "Bash(ruff *)",
      "Bash(mypy *)"
    ]
  }
}
```

**Do NOT add broad-form allows** like `Bash(npm *)`, `Bash(python *)`,
`Bash(pip *)`, `Bash(cargo *)`, `Bash(go *)`, `Bash(bun *)`. Those let
an agent run arbitrary `npm exec`, `python -c`, `pip install
<attacker-pkg>`, etc. and bypass the workspace's hardening. The
narrow-subcommand pattern is what makes the permission model
load-bearing.

This file is **per-machine** — gitignored by Claude Code convention. Each
teammate maintains their own.

### Stack-specific snippets

Pick the snippet that matches your stack. Mix for polyglot projects.

**Node / TypeScript:**

```json
{
  "permissions": {
    "allow": [
      "Bash(npm install)",
      "Bash(npm ci)",
      "Bash(npm test *)",
      "Bash(npm run *)",
      "Bash(npx tsc *)",
      "Bash(npx vitest *)",
      "Bash(npx jest *)",
      "Bash(npx eslint *)",
      "Bash(npx prettier *)",
      "Bash(npm audit *)",
      "Bash(npm outdated *)"
    ]
  }
}
```

**Python:**

```json
{
  "permissions": {
    "allow": [
      "Bash(pytest *)",
      "Bash(pip install -r *)",
      "Bash(pip-audit *)",
      "Bash(ruff *)",
      "Bash(mypy *)",
      "Bash(black *)",
      "Bash(uv pip *)",
      "Bash(uv run *)",
      "Bash(poetry run *)",
      "Bash(poetry install)"
    ]
  }
}
```

**Go:**

```json
{
  "permissions": {
    "allow": [
      "Bash(go test *)",
      "Bash(go build *)",
      "Bash(go vet *)",
      "Bash(gofmt *)",
      "Bash(govulncheck *)",
      "Bash(golangci-lint *)"
    ]
  }
}
```

**Rust:**

```json
{
  "permissions": {
    "allow": [
      "Bash(cargo test *)",
      "Bash(cargo build *)",
      "Bash(cargo check *)",
      "Bash(cargo clippy *)",
      "Bash(cargo fmt *)",
      "Bash(cargo audit *)"
    ]
  }
}
```

**Ruby:**

```json
{
  "permissions": {
    "allow": [
      "Bash(bundle install)",
      "Bash(bundle exec rspec *)",
      "Bash(bundle exec rubocop *)",
      "Bash(rake test*)",
      "Bash(rake db:migrate*)"
    ]
  }
}
```

**Container / DevOps tooling:**

```json
{
  "permissions": {
    "allow": [
      "Bash(docker build *)",
      "Bash(docker compose *)",
      "Bash(kubectl get *)",
      "Bash(kubectl describe *)",
      "Bash(kubectl logs *)",
      "Bash(helm lint *)",
      "Bash(helm template *)",
      "Bash(terraform fmt*)",
      "Bash(terraform validate*)",
      "Bash(terraform plan*)"
    ]
  }
}
```

Note: `kubectl apply`, `helm install`, and `terraform apply` are
deliberately not in any snippet. Those are state-changing and should
prompt every time. The release engineer uses them via the prompt-through
path.

---

## Step 5 — Fill `CONSTITUTION.md` §1 (Stack & boundaries)

`/init-project` leaves §1 as `_TBD_` placeholders deliberately. Until you
fill them, `spec-architect` emits an `URGENT: yes` CLARIFY on every
pipeline run, refusing to guess at the stack.

Open `CONSTITUTION.md`. The first section looks like:

```markdown
## 1. Stack & boundaries

- **Language(s) & runtime:** _TBD_
- **Framework(s):** _TBD_
- **Datastore(s):** _TBD_
- **External services we depend on:** _TBD_
- **Deployment target:** _TBD_
- **Supported clients / browsers / OSs:** _TBD_
```

Replace each `_TBD_` with a concrete answer. Concrete means "another
engineer reading this six months from now picks the right dependency on
the first try." Example for a Node service:

```markdown
- **Language(s) & runtime:** TypeScript 5.4 on Node 20 LTS. Strict mode
  on; `noUncheckedIndexedAccess` enabled. No `any` in committed code.
  ESM modules.
- **Framework(s):** Fastify 4.x (HTTP), Prisma 5.x (ORM), Zod 3.x (input
  validation), Vitest 1.x (test), Pino (structured logging).
- **Datastore(s):** PostgreSQL 16 (Supabase-managed). Redis 7 for
  short-lived state. No other persistent stores.
- **External services we depend on:** Stripe (payments), Resend (email),
  Sentry (errors), GitHub (OAuth).
- **Deployment target:** Fly.io single-region (fra) for v1.
- **Supported clients / browsers / OSs:** modern evergreen browsers,
  last 2 majors; mobile WebKit on iOS 16+. No IE11.
```

**Also fill §6 (Performance budgets) if your project is latency-sensitive.**
For a CLI tool or batch job, leave §6 as `_TBD_` — `performance-analyst`
falls back to structural checks.

See [`constitution.md`](constitution.md) for the full walkthrough.

---

## Step 6 — Commit the bootstrap

The bootstrap produced meaningful changes worth committing:

```
git add CLAUDE.md CONSTITUTION.md .claude/settings.local.json
git commit -m "Bootstrap <product-name>"
```

`CONSTITUTION.template.md` was deleted by `/init-project`; that removal
is already staged.

---

## Step 7 — Validate the install

Ask Claude something simple to verify the agents loaded:

> Which agents are available?

The response should list 17: requirements-intake, spec-architect,
developer, test-engineer, doc-writer, qa-reviewer, security-auditor,
performance-analyst, database-designer, devops-engineer, code-reviewer,
ux-consultant, dependency-auditor, refactor-specialist, release-engineer,
observability-auditor, backlog-curator.

If you see "agent not found" errors — `.claude/agents/` is incomplete;
re-clone.

If you see permission prompts during routine reads — that's normal for
operations not pre-allowed; read [`customizing.md`](customizing.md) for
what's expected.

---

## Step 8 — Run your first feature

With the constitution filled and the bootstrap committed:

```
/autopilot Build a /healthcheck endpoint that returns 200 OK and a JSON
body containing the service name, version (from package.json), and a
timestamp. Cache headers should mark it as non-cacheable.
```

The intake agent batches 4–10 clarifying questions. Answer them. The
pipeline runs intake → spec → code → tests → docs → reviewers → release.

See [`how-it-works.md`](how-it-works.md) for what happens at each phase.

---

## Worked example: TypeScript service end-to-end

A complete walkthrough from empty clone to first feature shipping.

```
$ git clone https://github.com/me/order-api.git
$ cd order-api
$ claude
```

(The clone was created via "Use this template" on the scaffold's GitHub
page, named `order-api` for the product.)

In Claude Code:

```
/init-project order-api
```

Output:

```
✓ `order-api` bootstrapped.

Created: CONSTITUTION.md (from template, project name filled in)
Removed: CONSTITUTION.template.md (no longer needed)
Updated: CLAUDE.md (Product line: order-api)

Next steps before /autopilot will accept work:
  1. Edit CONSTITUTION.md §1 (Stack & boundaries).
  2. If the project is latency-sensitive, fill §6 (Performance budgets).
  3. Create .claude/settings.local.json with stack-specific narrow allows.
  4. Run /autopilot <description of the first feature>.
```

Fill the constitution: open `CONSTITUTION.md`, set §1 to
TypeScript/Fastify/Postgres, §6 to 200ms p95.

Create `.claude/settings.local.json` with the Node snippet from Step 4.

Commit:

```
git add CLAUDE.md CONSTITUTION.md .claude/settings.local.json
git commit -m "Bootstrap order-api"
```

Run the first feature:

```
/autopilot Build a POST /orders endpoint that accepts a list of line
items and returns the created order with an id, status (always
"pending"), and timestamps. Persist to Postgres via Prisma. Emit an
`order_created` event.
```

Intake asks 4–6 questions. You answer. The pipeline runs:

- `spec-architect` writes `docs/specs/orders.md`,
  `docs/api/orders.openapi.yaml`, `docs/data-models/orders.md`.
- `database-designer` writes a migration.
- `developer` writes `src/orders/` modules.
- `test-engineer` writes tests, runs `npm test`.
- `doc-writer` replaces the scaffold `README.md` with the product README
  and adds `docs/api/orders.md`.
- The convergence loop runs: `qa-reviewer`, `code-reviewer`,
  `observability-auditor` always; `security-auditor` and
  `performance-analyst` because the change touches auth and queries.
- `release-engineer` creates a branch, opens a PR, waits for CI, deploys
  to staging, smoke-tests, verifies events.

Final report lands. Code in `src/`, tests in `tests/`, full audit trail
in `docs/`.

---

## Updating the scaffold

When agent-forge evolves and you want to pull improvements into your project, use
`/forge-update`. It shows you a diff of forge-owned files, asks for approval, and
applies only the scaffold files — never your `CONSTITUTION.md`, `CLAUDE.project.md`,
source code, or project artifacts.

**One-time setup:** add agent-forge as a git remote in your project:

```bash
git remote add forge-upstream <url-of-agent-forge-repo>
git fetch forge-upstream
```

Then whenever you want to update:

```text
/forge-update
```

The command will:
1. Compare your project's forge-owned files against `forge-upstream/main`.
2. Show a diff of what would change.
3. Run a **preflight gate** before apply: it blocks if any version in the
   upgrade range declares a `Requires` prerequisite your project is missing
   (e.g. a `CONSTITUTION.md` section an earlier manual step should have added),
   and hard-stops on any `⚠ BREAKING` version until you confirm you've read its
   migration guide.
4. Apply on your approval — forge-owned files only.
5. Print any manual steps needed for your `CONSTITUTION.md` (never auto-applied).

**What is forge-owned vs. project-owned:**

| Forge-owned (auto-updated) | Project-owned (never touched) |
| --- | --- |
| `.claude/agents/*.md` | `CONSTITUTION.md` |
| `.claude/commands/*.md` | `CLAUDE.project.md` |
| `.claude/templates/` | `src/`, `tests/`, `docs/` artifacts |
| `CLAUDE.md` | `.claude/settings.json`, `.claude/memory/` |

**If you don't have a git remote:** run `/forge-update` anyway and choose the manual
option — it will print the relevant `UPGRADING.md` entries and guide you through
applying each change by hand.

**Version tracking:** your project's `.forge-version` file records which forge version
it was bootstrapped from or last updated to. Check it with `cat .forge-version`.

---

## What to commit (and what not to)

Tracked:

- `CLAUDE.md`, `CONSTITUTION.md`, `README.md`
- `docs/**` (scaffold docs + product artifacts)
- `.gitignore`
- `.claude/agents/**`, `.claude/commands/**`, `.claude/settings.json`
- Everything under `src/`, `tests/`, `migrations/`, `infra/` — product
  code.

Not tracked:

- `.claude/settings.local.json` — per-machine.
- OS / editor noise (`.DS_Store`, `Thumbs.db`, `*.swp`, `.vscode/`,
  `.idea/`).
- Stack-specific build artifacts (uncomment the relevant section of
  `.gitignore` after you fill in `CONSTITUTION.md` §1).

---

## Common pitfalls

- **Forgot to run `/init-project`.** Agents see the `_template — ...`
  placeholder in `CLAUDE.md`'s `Product:` line and refuse work. Run
  `/init-project <name>`.
- **Forgot to fill §1.** Intake emits `URGENT: yes` until §1 is filled.
- **`settings.local.json` missing.** Every `npm test` / `pytest`
  invocation prompts. Add the narrow allows from Step 4.
- **Broad `Bash(npm *)` allow.** This works but destroys the security
  model. Use narrow forms.
- **Forgot to commit the bootstrap.** Not strictly required, but a clean
  checkpoint before the first `/autopilot` run helps.

---

## One repo per product

Each template clone = one product. To develop multiple products, clone
the template multiple times:

```
~/code/order-api/              (order-api product)
~/code/customer-portal/        (customer-portal product)
~/code/billing-ingest/         (billing-ingest product)
```

Each clone is independent: its own git repo, own `CONSTITUTION.md`, own
`.claude/settings.local.json`, own agent customizations. Costs a few MB
of disk per product; gains per-product `settings.local.json` with narrow
stack-specific allows (instead of a polluted union of every stack), and
mental-model alignment with VS Code workspaces, IDE projects, CI
runners — all of which assume one workspace = one project.

---

## Next step

You have a working product repo. The operations manual is in
[`how-it-works.md`](how-it-works.md).
