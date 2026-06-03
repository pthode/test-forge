# Intent — Why this scaffold exists

> **What this covers:** the philosophy behind the multi-agent pipeline. Why the
> work is split this way, what problems it is solving, what trade-offs it accepts.
>
> **When to read it:** first, if you want to know whether this scaffold fits your
> situation. Or later, when you are tempted to bypass a gate and want to remember
> what the gate was there for.

This document is candid about trade-offs. Read it once. The rest of the
documentation is operational; this is the only place that explains *why*.

---

## The problem this scaffold solves

A single Claude instance is a brilliant pair programmer with a short attention
span. It will:

- Write code before reading the spec, then notice the spec halfway through and
  refactor.
- Add tests that pass against the *current* implementation rather than the
  *intended* one.
- Skip documentation entirely unless reminded.
- Lose track of cross-cutting concerns — security, performance, observability,
  accessibility — because they are not the immediate task.
- Drift between conversations, re-deciding things you already decided.

A team of human engineers solves these problems with division of labor (spec
writer, developer, tester, reviewer, security, SRE), with written artifacts that
survive across conversations (specs, ADRs, runbooks, postmortems), and with
explicit gates (PR review, CI, security sign-off, release approval).

This scaffold gives Claude the same machinery. Seventeen agents with narrow
responsibilities. Written artifacts at each step (`/docs/specs/`,
`/docs/qa-reports/`, etc.). Explicit gates between stages. Structured handoff
blocks (`CLARIFY`, `REJECT`) that make disagreements visible instead of silently
papered over. A constitution that pins invariants you keep re-deciding.

The cost is overhead. A trivial change does not need a four-phase pipeline. The
scaffold acknowledges this with manual single-agent invocation as the alternative
to `/autopilot` — you invoke `developer`, `code-reviewer`, etc. directly for
one-shot work. The agents' own forbidden actions enforce the right discipline;
no separate "route" or pipeline ceremony is needed. For everything substantial,
the overhead pays for itself the first time the security auditor catches a
parameterized-SQL violation that the developer would have shipped, or the
observability auditor notices that a payment-failure path emits no log line.

---

## Five principles the scaffold encodes

These are the principles the pipeline structure expresses. If you understand
these, you can predict how any agent will behave without reading its definition.

### 1. The spec is upstream of code. The constitution is upstream of the spec.

`Constitution > Spec > Implementation > Tests > Docs.`

If two artifacts disagree, the higher one wins. Tests do not exist to assert
what the code currently does; they exist to verify what the spec requires.
Documentation does not invent features; it describes what the code does. A
spec that contradicts the constitution is itself wrong, and the agent that
notices rejects upstream instead of implementing the broken contract.

This precedence is what stops the pipeline from drifting into "whatever the
last agent wrote becomes the new truth." Every agent reads the constitution and
the spec. Every agent compares its artifact against those, not against the
output of the previous stage.

### 2. Clarifying questions are batched at one window.

Intake is the only place where the pipeline asks the user for input. Once
intake closes, the rest runs autonomously. Agents that find ambiguity emit a
`CLARIFY` block addressed to an upstream agent, and the orchestrator routes it
back — usually to `spec-architect`, occasionally to intake's locked ticket, only
rarely (`URGENT: yes`) to the human.

This matters because human latency dominates everything else. A pipeline that
prompts the user 15 times per feature is a pipeline that takes a day to ship
something a tight intake could have shipped in an hour. The batched-intake
discipline is what makes `/autopilot` feel autonomous rather than chatty.

### 3. Disagreements are made structural, not papered over.

When the developer thinks the spec is unclear, they emit a `CLARIFY` block.
When the test engineer finds the implementation contradicts the spec, they emit
a `REJECT` block. When QA finds the README disagrees with the code, they emit
a `REJECT` to the doc writer.

Structured blocks force the disagreement to surface as text, in a known format,
addressed to a specific agent. They cannot be hidden in a side comment or
silently corrected. The orchestrator routes them; the receiving agent must
respond.

This is the same discipline a good code review enforces: surface the
disagreement, name the responsible party, require an explicit resolution. The
scaffold makes it mechanical.

### 4. Reviewers run in parallel, in a fixpoint loop.

After implementation, code goes to a panel of reviewers — QA, code review,
observability, and (when applicable) security, performance, UX. They run in
parallel, not in sequence. Each surfaces issues as `REJECT` blocks. Issues get
routed to whoever owns the fix. Reviewers re-run. The loop terminates when no
`REJECT` block surfaces.

Parallel reviewers mean the security auditor never blocks the performance
analyst, and vice versa. Fixpoint iteration means an issue surfaced in one
round can be addressed before the next round, and re-flagged if the fix is
wrong.

A smart cap (three consecutive same-signature `REJECT`s, no-progress detection,
or eight iterations) prevents infinite loops on contradictory feedback. When
the cap fires, the orchestrator escalates to the human with a structured
summary of what is recurring. This is the second user-interaction window.

### 5. Permission is the moat.

The permission model in `.claude/settings.json` is not a friction-reduction
tool. It is the trust boundary. Agents can spawn other agents, write files
under the project tree, and execute narrow allow-listed Bash commands.
Everything else either prompts you or is hard-denied.

The deny list specifically blocks: editing the permission file itself, reading
secrets (`.env`, `.pem`, `.aws/`, `.ssh/`, etc.), code-execution evasion
(`python -c`, `bash -c`, `pwsh -Command`, etc.), executable surface modification
(`.git/hooks/`, `.husky/`, `.vscode/tasks.json`), and OS directories
(`C:\Windows`, `/etc`).

This means an agent that goes off the rails — through prompt injection,
hallucination, or a malformed instruction — cannot exfiltrate your AWS
credentials, rewrite its own permission rules, install a malicious git hook,
or call `python -c "import os; os.system(...)"`. The other gates (specs,
tests, reviewers) catch correctness problems; the permission model catches
catastrophe.

The cost is that adding new tooling (a different test runner, a new build
command, a deploy tool) requires editing `settings.local.json` by hand. That
is intentional. Convenience-driven broad allows are how trust boundaries get
eroded.

---

## What the scaffold is *not*

These are the misreadings that turn the scaffold into overhead with no payoff.

- **It is not a CI replacement.** The pipeline runs at authoring time; CI runs
  at integration time. The release engineer requires green CI before
  considering a release valid. Keep your CI.
- **It is not a code quality religion.** The code reviewer flags duplication,
  poor naming, and unjustified abstraction. It does not enforce a specific
  paradigm. If you write Go differently than Rust, that is fine; the
  reviewer's anchor is the constitution's §3, which *you* fill in.
- **It is not magic.** Every agent's behavior is defined in `.claude/agents/`,
  in plain prose. If you want to know why the security auditor flagged
  something, open `.claude/agents/security-auditor.md`. If you want it to
  behave differently, edit that file (and see [`customizing.md`](customizing.md)
  for the safety rules).
- **It is not designed for one-off scripts.** The structure assumes a real
  project with multiple features over time. A throwaway prototype does not
  benefit from this overhead. Use Claude Code without this scaffold for
  spikes.

---

## Trade-offs the scaffold accepts

Honest accounting of where the friction lives.

- **Time-to-first-output is higher than ad-hoc prompting.** The intake agent
  asks 4–10 questions before any code is written. For a small feature this
  feels slow. The payoff arrives in the convergence loop, when the reviewers
  do not surface 30 issues that a tighter spec would have prevented.
- **You must fill in the constitution.** Specifically §1 (Stack & boundaries).
  Until you do, intake refuses to lock a ticket. This is annoying the first
  time. It is the right discipline every time after.
- **You must write `settings.local.json` by hand.** The workspace
  `settings.json` denies agents from creating it for you, on purpose. Spend
  five minutes adding `Bash(pytest *)`, `Bash(npm test *)`, etc. once per
  machine, per project.
- **Some flexibility is gone.** The pipeline expects `/src/`, `/tests/`,
  `/docs/` layouts. If your project uses different conventions you will need
  to either adapt the layout or edit the agent definitions. This is friction
  for unusual stacks; for typical ones it is structure that helps.
- **Prompt injection in user requirements is a real attack vector.** An agent
  that reads a requirements ticket can be steered by content in that ticket.
  The permission model is the backstop: even a fully-injected agent cannot
  read your `.env` or call `bash -c`. But you should still treat requirements
  text as untrusted when third parties write it.

---

## When the scaffold pays for itself most

Two situations where the overhead is dramatically worth it.

**Multi-stakeholder features.** When a change touches the database, the API,
the frontend, security, and observability all at once, the pipeline keeps each
concern in view through a dedicated agent. The database designer enforces
two-phase migrations. The security auditor reads the auth code path. The
observability auditor confirms every spec failure-mode emits a log event. None
of these get forgotten because none of them are the developer's primary
attention.

**Long-running projects with multiple contributors.** The constitution and the
written specs become the project's institutional memory. A new contributor (or
a future-you who lost context) reads `/docs/specs/foo.md` instead of asking
"why is it like this?" The artifacts answer the question.

For a one-person spike, this is overhead. For a real project, it is the
documentation you would have wanted anyway, written by the agent that already
had the context.

---

## Further reading

- [`how-it-works.md`](how-it-works.md) — How the principles above become a runnable
  process, plus the agents reference.
- [`constitution.md`](constitution.md) — The upstream-of-everything document.
- [`customizing.md`](customizing.md) — Why the permission model looks the way it
  does, plus how to extend the scaffold safely.
