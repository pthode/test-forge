# Audit prompt

> **What this is:** a paste-ready prompt for running an independent, expert-
> level audit of the scaffold (or any project that has extended it). Run in a
> fresh Claude Code session, ideally in plan mode.
>
> **When to use it:** after a substantial refactor of the scaffold itself,
> periodically as a quality check, or when a teammate wants to verify the
> setup before adopting it. Product teams who customize the scaffold (new
> agents, modified routing, additional slash commands) should audit their
> customizations the same way — the audit dimensions are universal.

---

## How to use

1. **Open a fresh Claude Code session** at the repository root (so `CLAUDE.md`
   loads automatically). Use a fresh session, not the conversation you've
   been working in — the whole point is independent eyes.

2. **Enter plan mode** before pasting (Shift+Tab in most setups, or your
   keybinding for "Plan Mode"). Plan mode prevents the agent from making
   edits on its own initiative; the audit produces findings, you triage.

3. **Paste the prompt below**, verbatim. It is self-contained — it briefs
   the new session on what the scaffold is, what to audit, how to
   approach, and what output to produce.

4. **Review the findings before approving any fixes.** Plan mode's
   ExitPlanMode artifact presents what the audit found and (optionally) a
   proposed fix sequence. You approve the parts you want, reject the
   rest, or refine.

---

## The prompt (paste this)

```
I have a multi-agent Claude Code scaffold at this repository root that I want
you to audit independently and thoroughly. Use all your expert capabilities —
read systematically, dispatch subagents to parallelize, reason from first
principles. Do not assume prior work was correct; verify every invariant
against the actual files.

## Context

This repo is a flat-layout template for the agent-forge scaffold: clone
it, the clone IS the product repo, scaffold files coexist with product code.
Seventeen specialized subagents run a four-phase pipeline (Intake → Build →
Convergence → Release) with a constitution as upstream precedence
(Constitution > Spec > Implementation > Tests > Docs) and a hardened
permission model as trust boundary. `CLAUDE.md` is the router playbook; the
full manual is in `docs/`.

## Audit scope

Cover six dimensions. Use judgment for depth.

1. Correctness / internal consistency. Cross-reference paths, section
   numbers, schema fields, agent names, output artifacts across all files.
   Stale references from prior refactors are a known historical pattern.

2. Software-engineering best practices. Separation of concerns;
   forbidden-action clarity; two-phase migrations; test discipline;
   documentation as artifacts; explicit gates between stages.

3. Modern AI design (correctness side). Agent definition quality (clear
   role, minimum tool list, structured outputs); CLARIFY/REJECT structured
   handoffs as a pattern; appropriate subagent dispatch;
   convergence/self-correction loop design; constitution-as-context vs.
   spec-as-context boundary.

4. Security model. `.claude/settings.json` — allow/deny precedence;
   code-execution evasion (interpreters, Windows shells, stdin-fed forms);
   settings self-protection; secret reads; executable-surface denies;
   prompt-injection resistance.

5. Documentation quality. Voice, navigability, completeness, accuracy
   against the code. Reading-order coherence for a newcomer.

   **Doc-drift sweep (do this concretely, with counts).** The `docs/`
   manual duplicates facts whose source of truth is elsewhere; these are
   the first things to rot. Cross-check each against its authoritative
   source and report every mismatch as a correctness finding:

   - **Agent count.** Count `.claude/agents/*.md`. Every "N agents" /
     "N specialized agents" / "N agent definitions" phrase in `docs/` and
     this prompt must equal it.
   - **Agents reference.** Every agent file has an entry in
     `how-it-works.md` (role, triggers, outputs, forbidden actions) — none
     missing, none describing a removed agent.
   - **Routing table.** The table in `how-it-works.md` matches the one in
     `CLAUDE.md` row-for-row.
   - **Artifact maps.** The map in `how-it-works.md` matches the one in
     `CLAUDE.md`, and both match where agents actually declare they write.
   - **Constitution.** The section list, agent→section table, and prose in
     `docs/constitution.md` (and the guidance in `docs/customizing.md`)
     match the actual section numbers/titles in `CONSTITUTION.template.md`.
   - **Task flows.** `task-flows.md` diagrams describe handoffs that still
     match the agents' forbidden actions and the autopilot phase order.

   Treat any divergence as a `major` correctness finding — drift in the
   onboarding manual is what new contributors trust first.

6. AI/orchestration optimization (efficiency and cost side). Beyond
   correctness — where is the pipeline wasteful or suboptimal? Investigate
   each of:

   a) Token efficiency. Are agent definitions concise where they can be?
      Are CLARIFY/REJECT and report templates verbose? Could "Operating
      rules" be trimmed without losing binding behavior? Are there
      sentences of pure preamble that cost tokens on every invocation?
      Actually count tokens of each agent definition where you can.

   b) Prompt-caching opportunities. The Anthropic API supports prompt
      caching with a 5-minute TTL — static prefixes cache, dynamic
      suffixes do not. Are agent definitions structured cache-friendly
      (stable content first, volatile last)? Does the constitution get
      re-read per agent invocation when it could be cached and passed by
      reference? Does the convergence loop's reviewer re-invocation reuse
      cached context across iterations?

   c) Agent-context bloat in Phase 2 handoffs. Phase 2 accumulates
      context sequentially: ticket → spec-architect → developer
      (receives ticket + spec + specialist outputs) → test-engineer
      (receives ticket + spec + /src/ paths) → doc-writer (receives spec
      + impl + tests). Where is this redundant? Are agents handed full
      artifacts when summaries would suffice? Could autopilot.md specify
      summary-based handoffs explicitly? Estimate the typical Phase 2
      context size for a medium feature.

   d) Pipeline telemetry. The scaffold has no record of how long each
      phase took, how many tokens each agent consumed, which
      CLARIFY/REJECT signatures recurred most often, or which agents
      fired most. Should it? What would minimum viable telemetry look
      like? Where would it live (a state file, a markdown trail, a
      separate JSONL log)?

   e) Convergence loop economics. Each Phase 3 iteration re-invokes 3–7
      reviewers in parallel. Is fail-fast cheaper (run qa-reviewer first,
      gate the rest on its pass)? Is parallel-always actually optimal,
      or wasteful when qa-reviewer alone often catches everything?

   f) Subagent dispatch overhead. Each Agent call has cost (system-prompt
      load, context handoff, isolated tool environment). Could two
      narrow reviewers be merged into one multi-lens pass? Or is
      separation-of-concerns load-bearing for output clarity? Where is
      the right trade-off?

   g) Context-window safety for long projects. As a project accumulates
      artifacts (many specs, many reports), agent reads grow. Does any
      agent risk hitting context limits when reading exhaustively rather
      than selectively? Is there a defined strategy for "latest spec
      only" vs. "full project history"?

   For each optimization finding, distinguish:
   - Measurable issue (you can demonstrate the waste with numbers).
   - Plausible-but-unverified hypothesis (worth investigating but not
     proven).
   - Architectural trade-off (cost is real but the design choice is
     defensible).

   Don't speculate. Flag uncertainty explicitly when you can't
   demonstrate the issue. Where concrete measurement is possible (token
   counts of agent files, estimated context-handoff sizes), do the
   measurement rather than hand-waving.

## Where to look

- `CLAUDE.md` — router playbook, canonical path-resolution rules.
- `CONSTITUTION.template.md` (or `CONSTITUTION.md` if `/init-project`
  has been run) — invariants template / project invariants.
- `.claude/agents/*.md` — 17 agent definitions.
- `.claude/commands/autopilot.md`, `init-project.md` — orchestration &
  bootstrap.
- `.claude/settings.json` — permission model.
- `docs/*.md` — 8-file operations manual:
    `README.md` (index), `intent.md`, `getting-started.md`,
    `how-it-works.md`, `task-flows.md`, `constitution.md`, `customizing.md`,
    `troubleshooting.md`.
- `README.md`, `.gitignore` — landing + scaffold tracking.

## How to approach

- Recent refactor history (most likely places for stale references):
  1. Nested→flat repo layout. The scaffold previously hosted nested
     `<project>/` directories with their own constitutions; it now uses
     a flat layout where the repo IS the product.
  2. Phase 4 (Release) added to `/autopilot`. The pipeline went from 3
     phases to 4. Some references to "three phases" may linger.
  3. Route taxonomy collapsed. The scaffold previously had "trivial-
     change route" and "bug-fix route" as named entities; both removed.
     Now: `/autopilot` for features, manual single-agent for everything
     else.
  4. State-file schema simplified. Was `phase3_iteration` +
     `phase4_iteration` + `iteration_totals` arrays + `signatures[*].phase`
     field. Now: single `iteration` counter scoped by `status` field;
     `iteration_totals` removed; `signatures` map resets at phase
     transition.
  5. Docs consolidated from 11 files to 7. Deleted: `installation.md`,
     `new-project.md`, `existing-project.md`, `pipeline.md`,
     `agents-reference.md`, `security-model.md`, `extending.md`. Merged
     respectively into `getting-started.md`, `how-it-works.md`, and
     `customizing.md`.

  Look for orphan links pointing at deleted files or fields. Look for
  prose that describes the old structure as if it still applied.

- Read systematically. Don't skim. Cross-cutting invariants only become
  visible when you read multiple files together.

- Parallelize with subagents where it helps (e.g., one agent auditing
  settings.json security while another cross-checks agent definitions
  while another counts tokens). Summarize their findings in your own
  words rather than pasting raw output — keep your context clean.

- For dimension 6, measure where you can. Token counts of agent
  definitions are knowable. Approximate context-handoff sizes for typical
  Phase 2 flows are knowable. Don't hand-wave when concrete numbers are
  available.

- Don't ask permission to read files; auditing is read-only by nature.

- Reason from first principles. Treat prior work as unverified.

- This audit should run in PLAN MODE. The output is a plan: findings
  first, then proposed fix sequence. Do not edit any files until I
  explicitly approve the plan via ExitPlanMode. If you find something
  worth flagging but not worth fixing yet, include it in the plan
  tagged "noted, no action."

## Output

A scannable senior-engineer report:

1. Strengths — what the scaffold does well (so I know what NOT to
   change).

2. Correctness findings — categorized blocker / major / minor / nit,
   each with:
   - `file:line` citation
   - One-line description of the issue
   - Concrete remediation

3. Optimization findings (dimension 6) — separately categorized as:
   - measurable waste (with the measurement)
   - plausible hypothesis (with what would prove or disprove it)
   - architectural trade-off (with the cost and the design rationale you
     inferred)
   Each tagged with the sub-dimension it touches (token / caching /
   context-bloat / telemetry / convergence-economics / dispatch /
   context-window) and a concrete recommendation if any.

4. Modern-AI / best-practice observations not covered above —
   improvements that aren't bugs but would meaningfully strengthen the
   scaffold.

5. Skipped with justification — anything that looks like an issue but
   you decided to leave, with reasoning.

Tone: direct, evidence-based, no marketing. Section headers, bullets,
sparse prose.

Begin.
```

---

## Customizing the prompt for your product

If you've extended the scaffold (added agents, modified routing, added
slash commands), update the prompt before running:

- **"17 specialized subagents"** → your actual agent count.
- **"four-phase pipeline"** → your actual phases if you changed them.
- **"8-file operations manual"** with the file list → your actual
  `docs/` contents.
- **Recent refactor history** → replace with *your* recent changes (the
  scaffold's history is irrelevant once you've forked).

The audit dimensions (1–6) and the plan-mode workflow stay the same.
