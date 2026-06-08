# Forge test protocol

A repeatable way to exercise agent-forge end-to-end in this throwaway project
and compare two forge versions. It measures the **efficiency/interruption
profile** (cost, time, review-loop length) automatically, and leaves the
**correctness + over-asking** judgments to a short human checklist — because
those are not reliably extractable from the transcript.

## What this can and cannot tell you

| Question | How it's answered | Reliability |
|---|---|---|
| Token cost, wall-clock, review rounds | `measure_run.py` (transcript) | good, but 1 run = 1 sample |
| Did the pipeline **over-ask** (technical-method questions)? | by hand: ticket §13 vs §14 | high — robust to run variance |
| Did it disclose autonomous decisions? | by hand: "Decisions taken" in final report | high |
| Did every phase run (structural completeness)? | by hand: `ls docs/` | high |
| Did it build the *right* thing (functional correctness)? | human judgment of code + tests | only a human can say |

Two honest caveats baked into the comparison:

1. **One run is a stochastic sample.** Token/time numbers vary run-to-run on the
   *same* version. Treat a <~15% delta as noise; run the fixture 2–3× per
   version before trusting a token/time difference. The over-asking signal is
   the exception — it's robust enough for one run.
2. **A version diff conflates every change** between the two versions, not only
   the one you care about. For the over-asking question that's fine
   (decision-surfacing landed in 1.15.0); for token/time it's directional only.

## Procedure

Run this from a Claude Code session opened **inside this project** (the
orchestrator under test is that session). One run:

1. Record the version: note the contents of `.forge-version`.
2. Start the feature:
   `/autopilot <paste the request block from fixture-lru-cache.md>`
3. In the intake window, answer per the **answer-key** in
   `fixture-lru-cache.md`. Crucially: for any *technical-method* question, give
   the "your call" answer and **write down that it was asked** — that tally is
   the over-asking metric.
4. Let the pipeline run to completion (RELEASED, or escalation).
5. Capture the automated profile:
   `python test-harness/measure_run.py`
   → prints the table and writes `run-<version>-<session>.json`.
6. Fill in the human checklist below for this run.

## Baseline → compare

- **Baseline (now, on the current `.forge-version`):** do the procedure once
  (ideally 3×). Keep the `run-*.json` files.
- **Update the forge**, then do the procedure again on the new version.
- Diff: `python test-harness/measure_run.py --compare run-<old>.json run-<new>.json`

## Per-run human checklist (copy one block per run)

```
RUN: version=______  session=________  date=________

OVER-ASKING (the headline metric)
[ ] # questions asked in intake total:            ___
[ ] of those, # that were PRODUCT/requirements:   ___
[ ] of those, # that were TECHNICAL-METHOD:       ___   <- want 0
[ ] list any technical-method questions asked:
        - ...

DISCLOSURE
[ ] final report contained a "Decisions taken & assumptions" list   (Y/N)
[ ] the autonomous technical choices (data structure, thread-safety,
    eviction impl) appear there with a one-line rationale            (Y/N)

STRUCTURAL COMPLETENESS  (ls docs/ ; ls src/ ; ls tests/)
[ ] requirements ticket written        docs/requirements/*.md        (Y/N)
[ ] spec written                       docs/specs/*.md               (Y/N)
[ ] code written                       src/tokenlab/cache.py         (Y/N)
[ ] tests written + passing            tests/unit/test_cache.py      (Y/N)
[ ] qa verdict APPROVED                docs/qa-reports/*.md          (Y/N)
[ ] release report                     docs/release-reports/*.md     (Y/N)

CORRECTNESS (skim, human judgment)
[ ] code actually implements bounded LRU with the agreed semantics   (Y/N)
[ ] tests cover eviction + stats + the ValueError on bad capacity    (Y/N)

AUTOMATED PROFILE (from measure_run.py)
    wall-clock: ___ min   qa rounds: ___   subagents: ___
    cost-wt input-equiv: ___   output tokens: ___
```

## Reading the result

- **Over-asking present** (technical-method count > 0 on the current version):
  evidence the discipline needs enforcing in `requirements-intake`, not just in
  CLAUDE.md / spec-architect. That's the surgical fix discussed in agent-forge.
- **Over-asking absent on new version but present on old:** the 1.15.0
  decision-surfacing change is doing its job; no forge change needed.
- **Cost/time materially lower on a "small feature" lane** (if/when one exists):
  evidence for the small-vs-large differentiation. Not testable until such a
  lane is built — out of scope for this fixture.
