# Troubleshooting

> **What this covers:** the failure modes you are most likely to hit, with
> concrete diagnoses and fixes. Convergence loops that stall, prompt floods,
> agents that contradict each other, Windows-specific gotchas, and common
> mistakes in `settings.local.json`.
>
> **When to read it:** when something is not working. This is a reference,
> not a tutorial — jump to the section that matches your symptom.

Each entry follows the same shape: **Symptom · What is happening · How to
fix it.**

---

## Pipeline / convergence problems

### Convergence loop never terminates

**Symptom.** Phase 3 has been running for more than ~10 minutes; reviewers
keep flagging issues; the orchestrator has not produced a final report.

**What is happening.** The convergence loop has a smart cap. It escalates
to you when:

- The same finding signature appears in three consecutive iterations
  (no-progress).
- Total REJECT count did not decrease and no signature changed.
- Iteration count reaches eight.

If you are seeing prolonged Phase 3 activity, one of these has not yet
fired but is close. Wait for the escalation message — the orchestrator
prints a recurring-findings summary on cap fire and stops.

**How to fix.** When the escalation prints, read the recurring-findings
summary. The most common patterns:

1. **Two reviewers contradict each other.** Security wants shorter
   sessions; UX wants longer sessions. No automatic resolution is
   possible. You decide, then either update the constitution (§5 or §7)
   to encode the decision, or update the spec to reflect it.
2. **The fix loop is unproductive.** Developer fixes the symptom but not
   the cause; the next iteration flags it again at a slightly different
   line. Read both REJECTs and update the spec to be more specific about
   the intent. Re-run.
3. **The spec is wrong, not the code.** Each reviewer is correct about a
   spec section that should change. REJECT to `spec-architect` and amend
   the spec; the implementation does not need to change.

If you have escalated **multiple times in a row** on the same feature,
suspect that the constitution does not actually capture the rules you
want enforced. Read [`constitution.md`](constitution.md) and consider
amending §2, §3, or whichever section the reviewers keep citing.

### Reviewer keeps flagging the same issue after the developer "fixed" it

**Symptom.** `security-auditor` says `src/auth/login.ts:88 uses MD5`; the
developer fixes it to use bcrypt and reports done; the next iteration
flags `src/auth/login.ts:90` for the same issue.

**What is happening.** The signature hash strips line numbers, so a
re-flag at a shifted line **does** hash identically — that case escalates
correctly. But if the issue truly **was** moved (rather than fixed), the
shifted-line hash matches and the no-progress detector fires after three
iterations. That is the intended behavior.

**How to fix.** Read the second REJECT in detail. If the issue moved to
a new file rather than being fixed, the developer's fix was incomplete.
Route the REJECT back to `developer` with explicit "fix the actual
problem, not the symptom" instruction.

If the reviewer is wrong (the second occurrence is a different issue that
happens to use the same pattern), the convergence loop will not let you
say so cleanly. Best path: invoke the reviewer manually with a more
specific scope, get its report, and reconcile in chat.

### Phase 1 intake asks unfamiliar questions

**Symptom.** You ran `/autopilot Build me a /healthcheck endpoint` and
intake asks about "rate-limit thresholds" and "OpenTelemetry trace
propagation".

**What is happening.** `requirements-intake` reads the constitution
before asking questions. If §8 (observability) requires trace IDs and
§5 (security) implies rate limits on public endpoints, intake will ask
how they should apply to your new feature even if you did not mention
them.

**How to fix.** This is intake doing its job. Answer the questions; the
batched-intake discipline is what prevents these from coming up
mid-pipeline. If the question genuinely does not apply ("no, this
endpoint is internal only"), say so — intake records "N/A" with your
reason and the downstream agents see it.

### Spec-architect emits `URGENT: yes` on every run

**Symptom.** Every `/autopilot` run starts with `spec-architect` asking
the user a question — usually about the stack.

**What is happening.** Constitution §1 (Stack & boundaries) is still
`TBD` (or partially `TBD`). The spec architect refuses to guess at
stack-level decisions; it emits an URGENT CLARIFY to surface the gap.

**How to fix.** Open `CONSTITUTION.md`, fill in every `_TBD_`
in §1. See [`constitution.md`](constitution.md) for the worked example.
After you fill §1, re-run `/autopilot`; the urgent escape stops firing.

---

## Permission / prompt problems

### Every test run prompts for permission

**Symptom.** Each time `test-engineer` or `qa-reviewer` runs `npm test`
or `pytest`, Claude Code prompts: "Allow this Bash command?"

**What is happening.** Your stack's test runners are not in
`.claude/settings.local.json`. The workspace `settings.json` is
project-agnostic — it does not auto-allow `Bash(npm test *)` or
`Bash(pytest *)` because the stack is unknown at scaffold time. You
need to add the narrow allows in your per-machine file.

**How to fix.** Create or edit `.claude/settings.local.json` and add the
narrow allows for your stack. Snippets in
[`getting-started.md`](getting-started.md).

Example for Node:

```json
{
  "permissions": {
    "allow": [
      "Bash(npm test *)",
      "Bash(npm run *)",
      "Bash(npx tsc *)",
      "Bash(npx vitest *)"
    ]
  }
}
```

**Do NOT** "fix" this with `Bash(npm *)` or `Bash(node *)`. Those are
arbitrary code execution. See
[`customizing.md`](customizing.md).

### Agent fails with "denied by your permission settings"

**Symptom.** An agent reports: "File is in a directory that is denied
by your permission settings" or "Command is denied by your permission
settings."

**What is happening.** The agent tried an operation matching a `deny`
rule. This is the trust boundary working as designed. Common
triggers:

- Trying to read `.env`, `*.pem`, `.aws/`, `.ssh/`, etc. (secret reads).
- Trying to edit `.claude/settings.json` or `.claude/settings.local.json`
  (settings self-protection).
- Trying to run `bash -c`, `python -c`, `pwsh -Command`, etc.
  (code-execution evasion).
- Trying to write to `.git/hooks/`, `.husky/`, `.vscode/tasks.json`
  (executable surfaces).

**How to fix.** Identify which rule fired (the error message names the
file or command). Decide whether:

- The agent is doing something it should not. Edit the agent definition
  to forbid the action explicitly, or constrain its scope.
- The operation is legitimate and your `settings.json` needs adjustment.
  Edit the file by hand, going through the security-auditor review path
  documented in [`customizing.md`](customizing.md).

Do **not** broad-allow your way out of denies. The denies are the most
load-bearing rules in the scaffold.

### Browser prompt fatigue mid-run

**Symptom.** A single `/autopilot` run produces 30+ permission prompts.
You click through each one but the experience is miserable.

**What is happening.** Your `settings.local.json` is too narrow. The
agents are routinely hitting commands you have not pre-allowed.

**How to fix.** After the run, audit which commands prompted. The
common offenders:

| Prompt | Add to `settings.local.json` |
|--------|------------------------------|
| `npm test` (different scripts) | `Bash(npm test *)`, `Bash(npm run *)` |
| `npx tsc --noEmit` | `Bash(npx tsc *)` |
| `pytest tests/` | `Bash(pytest *)` |
| `mypy src/` | `Bash(mypy *)` |
| `cargo build --release` | `Bash(cargo build *)`, `Bash(cargo test *)` |
| `docker build .` | `Bash(docker build *)` |
| `gh pr checks --watch` | already in workspace `settings.json` |

Each addition should be the **narrowest form** that covers what you saw
prompted. If `npm run test:unit` and `npm run lint` both prompted,
`Bash(npm run *)` covers both. Do not add `Bash(npm *)`.

### Edits to agent definitions always prompt

**Symptom.** Every edit to `.claude/agents/*.md` triggers a permission
prompt, even though the file is inside the broadly-allowed workspace
tree.

**What is happening.** Claude Code applies a built-in confirmation
prompt to writes inside `.claude/`, regardless of allow rules. The
`.claude/` directory is the agent's own configuration surface — agents
that can silently rewrite their own definitions can self-modify in ways
the user never approved. This is enforced by Claude Code itself, not
the scaffold's permission rules.

**How to fix.** You cannot disable this prompt. It is the right
behavior — agent files are too sensitive to auto-write. Click through
the prompts when you are intentionally modifying agents.

If a script needs to bulk-modify agent files (e.g., the security-
auditor finds an issue across many files), it is preferable to apply
the changes yourself in the editor rather than approving N prompts in
a row.

---

## Constitution problems

### "Failed to lock ticket: constitution §1 is still TBD"

**Symptom.** `requirements-intake` returns an URGENT CLARIFY at the
end of Phase 1, asking you to fill in §1 before it can lock a ticket.

**What is happening.** The constitution is the highest-precedence
document. Locking a ticket without a stack decision means every
downstream agent will guess at the stack, and guesses are wrong far
more often than they are right.

**How to fix.** Open `CONSTITUTION.md`, fill in every
`_TBD_` in §1. See [`constitution.md`](constitution.md) for the worked
example. Re-run `/autopilot`.

### Agent rejects my spec citing the constitution

**Symptom.** `security-auditor` (or `database-designer`, or another
agent) emits a REJECT to `spec-architect` saying the spec contradicts
constitution §X.

**What is happening.** This is the constitution-precedence rule firing.
Every agent reads the constitution before producing artifacts; when
the spec asks for something §X forbids (e.g., MD5 for password hashing,
single-phase column drop, plaintext credentials in `.env.example`),
the agent rejects upstream rather than implementing the contradiction.

**How to fix.** Two options:

1. **Fix the spec.** Usually the right call. The spec is wrong; rewrite
   it to comply with the constitution. Route the REJECT back to
   `spec-architect`, who will update the spec.
2. **Amend the constitution.** Rare, but correct when the constitution
   itself is wrong (e.g., your new payment-processor integration
   genuinely requires a different crypto choice). Follow the §11
   amendment process documented in [`constitution.md`](constitution.md).

Do **not** bypass the rejection. The constitution is enforced for a
reason; the rejection is the mechanism.

---

## Routing / agent-invocation problems

### Router does the work itself instead of delegating

**Symptom.** You asked Claude to "review this code" and instead of
invoking `code-reviewer`, it analyzed the file inline and gave you a
review in chat.

**What is happening.** The router stepped out of its lane. It is
supposed to delegate every non-trivial task to a specialist.

**How to fix.** Prompt explicitly: "Use the `code-reviewer` agent on
[file]. Do not review inline."

If this happens repeatedly across sessions, the router's reading of
CLAUDE.md may be stale or unclear. Check that CLAUDE.md's "Your job as
router" section is intact:

> 1. Read the user's request. Identify the right agent (use the
>    routing table).
> 2. Hand off the full context to that agent via the Task/Agent tool.
> 5. **Do not** synthesize, write code, write tests, or write docs
>    yourself.

If the section has been edited or removed, restore it.

### Wrong agent gets invoked for ambiguous phrasing

**Symptom.** You said "look at the auth code" and the router invoked
`code-reviewer`; you wanted `security-auditor`.

**What is happening.** "Look at" is ambiguous. The routing table maps
trigger phrases to agents, but no table is perfect for natural
language.

**How to fix.** Use a specific trigger phrase:

- "Security review the auth code" → `security-auditor`.
- "Code review the auth code" → `code-reviewer`.
- "Performance review the auth code" → `performance-analyst`.
- "Run security-auditor on src/auth/" → explicit, unambiguous.

When in doubt, name the agent.

### Agent says "spec not found" but I have one

**Symptom.** The developer or test engineer reports it cannot find
the spec, but you can see `docs/specs/foo.md` exists at the
repository root.

**What is happening.** Two common causes in the flat layout:

1. The agent is looking for the spec under a different feature slug
   than what your file is named. E.g., the spec was written to
   `docs/specs/order-api.md` but the agent looking for the
   `place-order` feature does not find it under that name.
2. The agent is operating in a stale conversation that predates the
   spec being written. The spec exists on disk but is not in the
   agent's working context.

**How to fix.** For (1), align the feature slug — either rename the
file or refer to the feature by the slug the spec uses. For (2),
start a fresh conversation; the agent will rediscover the spec on
disk.

---

## Windows-specific gotchas

### Path separators in `settings.json`

**Symptom.** A deny rule like `Edit(**/.claude/settings.json)` does
not seem to fire on Windows when the actual path uses backslashes.

**What is happening.** Claude Code's permission engine normalizes
path separators (forward slash ↔ backslash) for glob matching, so the
forward-slash patterns should match. The scaffold's `settings.json`
includes **backslash mirrors** of the critical rules as belt-and-
suspenders against a future engine-normalization regression.

**How to fix.** Verify the deny rule has both forms:

```
"Edit(**/.claude/settings.json)",
"Write(**/.claude/settings.json)",
"Edit(**\\.claude\\settings.json)",
"Write(**\\.claude\\settings.json)"
```

If only the forward-slash form is present, add the backslash mirror.
The mirrors are documented in [`customizing.md`](customizing.md).

### PowerShell as the default shell

**Symptom.** A deny rule like `Bash(bash -c *)` blocks `bash -c`
calls, but agents on Windows machines run PowerShell by default and
the deny does not seem to apply.

**What is happening.** Claude Code's Bash tool on Windows actually
uses Git Bash (or WSL bash) by default, so `Bash(bash -c *)` does
apply. But the scaffold also denies `Bash(pwsh *)`, `Bash(powershell *)`,
`Bash(cmd /c *)`, `Bash(cmd.exe *)` because PowerShell/cmd are
arbitrary-code-execution vectors if any agent reaches for them.

**How to fix.** Verify the deny list includes all four:

```
"Bash(pwsh *)",
"Bash(powershell *)",
"Bash(cmd /c *)",
"Bash(cmd.exe *)"
```

If one is missing, add it. These cover the four common ways to invoke
a Windows shell.

### File-path matching with absolute Windows paths

**Symptom.** An allow rule like
`Edit(z:\\pt\\agent-forge\\**)` does not match writes
to files inside that directory.

**What is happening.** Two common causes:

1. The actual workspace lives at a different absolute path (a teammate
   forked the scaffold to a different machine). The absolute path in
   `settings.json` is local-specific.
2. The drive-letter case mismatches. Windows is usually case-insensitive
   for file paths, but the permission engine may not normalize case
   the same way the OS does.

**How to fix.** Verify the absolute path in `settings.json` matches
your local workspace path exactly. If it does not, update it. For a
forked scaffold on a new machine, update the absolute paths near the
top of `settings.json`:

```json
"Edit(z:\\pt\\agent-forge\\**)",
"Write(z:\\pt\\agent-forge\\**)",
"Edit(C:\\Users\\<you>\\.claude\\projects\\<workspace-id>\\memory\\**)",
"Write(C:\\Users\\<you>\\.claude\\projects\\<workspace-id>\\memory\\**)"
```

The memory directory's `<workspace-id>` follows Claude Code's
workspace-hash convention; check what Claude Code creates for you and
match it.

---

## State / file-on-disk problems

### Convergence state file does not exist

**Symptom.** Phase 3 says it cannot read
`docs/.autopilot-state/<feature>.json`.

**What is happening.** The first time Phase 3 runs on a feature, the
state file does not exist yet — that is normal. The orchestrator
creates it at the end of iteration 1.

If the message persists after iteration 1, the orchestrator may not
have write permission to `docs/qa-reports/`, or the directory
does not exist.

**How to fix.** Check the directory exists:

```
ls docs/qa-reports/
```

If it does not, create it:

```
mkdir -p docs/qa-reports/
```

The orchestrator should now be able to write the state file.

### CLAUDE.md still says `Product: _template — ..._` after I started working

**Symptom.** Agents emit `URGENT: yes` CLARIFY saying the repo is
still a fresh template clone; `/autopilot` refuses to lock a ticket
even though you have written code in `src/`.

**What is happening.** You skipped or partially ran `/init-project`.
The `Product:` line in `CLAUDE.md` is the signal agents use to know
whether the repo has been bootstrapped. While it still reads
`_template — ...`, agents treat the repo as not-yet-ready.

**How to fix.** Run `/init-project <product-name>` in Claude Code.
It renames `CONSTITUTION.template.md` to `CONSTITUTION.md`, removes
the template, and updates the `Product:` line. After that, agents
will accept work.

### `CONSTITUTION.template.md` was deleted but `CONSTITUTION.md` does not exist

**Symptom.** Neither file exists at the repository root. Agents fail
to read the constitution.

**What is happening.** `/init-project` was interrupted mid-run, or
the constitution file was deleted by mistake.

**How to fix.** Recover from git history:

```
git log --diff-filter=D -- CONSTITUTION.template.md
git checkout <commit-hash>~1 -- CONSTITUTION.template.md
```

Then re-run `/init-project <product-name>` to regenerate
`CONSTITUTION.md` from the template.

---

## Output / artifact problems

### Spec was written to the wrong path

**Symptom.** You expected the spec at `docs/specs/foo.md`; it landed
somewhere else (a sibling directory, a different feature slug, the
repository root).

**What is happening.** Either the agent miscomputed the path (rare;
usually a hand-modified agent that hard-coded a different path), or
the spec was filed under a feature slug different from what you
expected (e.g., `place-order` vs. `orders`).

**How to fix.** Look at `.claude/agents/spec-architect.md` — it
should reference `/docs/specs/<feature>.md`, with the leading slash
resolving to the repository root (per the path-resolution rule in
`CLAUDE.md`).

Move the misplaced file to the correct location by hand. If the
agent is hand-modified and the path resolution is broken, restore
the agent's `Output artifacts` section to use the leading-slash
convention.

### CHANGELOG not updated after a feature ships

**Symptom.** `release-engineer` reported the feature shipped, but
`CHANGELOG.md` does not have a new entry.

**What is happening.** `doc-writer` writes the CHANGELOG. If
`doc-writer` was skipped (manual direct-agent invocation outside
`/autopilot`), the CHANGELOG was not updated.

**How to fix.** Invoke `doc-writer` directly after the fact:

> Run `doc-writer` to add a CHANGELOG entry for the recently-shipped
> `<feature>`. Read the PR description and the release report at
> `docs/release-reports/<feature>-<date>.md` for context.

`doc-writer` will append the appropriate entry to the CHANGELOG.

---

## Performance problems

### `/autopilot` runs much slower than expected

**Symptom.** A feature you expected to take ~20 minutes is taking an
hour or more.

**What is happening.** A few common causes, in rough order of
likelihood:

1. **Permission prompts.** Each prompt blocks the pipeline until you
   click through. Twenty prompts at 30 seconds each is 10 minutes of
   wall-clock delay. Audit `settings.local.json` (see "Every test run
   prompts for permission" above).
2. **Convergence loop iterating many times.** Each Phase 3 iteration
   re-runs every reviewer. Eight iterations is the cap, but six is
   common when the spec is ambiguous. Each iteration is ~3–5 minutes.
3. **Test suite is slow.** `test-engineer` and `qa-reviewer` both run
   the full suite. If your suite takes 5 minutes, that is 10 minutes
   added to the run.
4. **CI is slow.** `release-engineer` waits for CI to go green. If CI
   takes 15 minutes, that is 15 minutes added to Phase 4.

**How to fix.** Address the causes in order. For 1, fix
`settings.local.json`. For 2, tighten the intake answers and the spec.
For 3 and 4, optimize the suite and CI themselves — Claude cannot
make your test suite faster.

### Single agent invocation is very slow

**Symptom.** Running `qa-reviewer` manually takes 15 minutes.

**What is happening.** `qa-reviewer` cross-checks ticket, spec, code,
tests, and docs, and runs the full test suite. On a large project,
this is genuinely a lot of reading and one expensive test run.

**How to fix.** Use the agent's narrower forms. Instead of
"qa-reviewer on the whole project", invoke `qa-reviewer` on a specific
feature: "Run `qa-reviewer` on the `/orders` feature only; the spec
is at `docs/specs/orders.md`." The agent will scope itself.

---

## When all else fails

Some failures do not match any of the patterns above. Triage:

1. **Read the agent's chat output carefully.** Most failures are
   announced by the agent in a sentence or two before the silence.
2. **Read the agent's report file.** If the agent produced a report
   to `/docs/*/`, the report often explains what blocked further work.
3. **Read the agent definition.** `.claude/agents/<agent>.md` lists
   forbidden actions and operating rules. Often a failure is the
   agent correctly refusing to do something its rules forbid.
4. **Read CLAUDE.md.** The router's behavior is fully documented
   there. If the router is doing something surprising, the surprise
   is usually documented.

If none of those clarify, the failure may be a genuine bug. Report it
in the scaffold's issue tracker with:

- The exact command or prompt you ran.
- The exact agent output you got back.
- The contents of the relevant files (constitution, spec, etc.).
- Your `settings.json` and `settings.local.json` (redact any
  machine-specific paths if they are sensitive).
