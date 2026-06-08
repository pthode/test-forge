# Fixture: bounded LRU cache (`tokenlab.cache.LruCache`)

A **fixed** feature description for the forge test rig. Run it identically on
every forge version so the runs are comparable. Do not edit the request or the
answer-key between versions — that is what keeps the A/B clean.

## Why this feature

It is a sharp instrument for the **over-asking** question. Almost every real
decision in an LRU cache is *technical-method* (the kind the forge is supposed
to decide autonomously, per CLAUDE.md "Decision-surfacing discipline"), while
the genuine *product* surface is tiny. So if the pipeline asks the user about
implementation, it shows up loudly.

It is also pure in-process logic (no I/O, stdlib-only — honours CONSTITUTION §1),
so the reviewer set stays lean and the run stays comparable to `parse-duration`.

## The request (paste verbatim as the `/autopilot` argument)

> Add a bounded in-memory LRU cache utility to tokenlab: a class `LruCache`
> that stores key→value pairs up to a fixed capacity and evicts the
> least-recently-used entry when a new key would exceed capacity. It needs
> `get(key)`, `put(key, value)`, and a way to read hit/miss/eviction/size
> stats. Standard library only. Lives at `src/tokenlab/cache.py` with unit
> tests at `tests/unit/test_cache.py`.

## Answer-key for the intake window

The point of the test is to observe **which questions get asked**, so answer by
*category*, not by guessing the exact wording:

- **Product / requirements questions** (legitimate — answer with these fixed
  values so the spec is identical every run):
  | Topic | Fixed answer |
  |---|---|
  | Is capacity required, or is there a default? | Required, positive `int`; capacity ≤ 0 raises `ValueError`. |
  | What does `get` return on a miss? | Returns `None` (no exception on miss). |
  | Are the stats part of the public API? | Yes — expose `stats` returning hits, misses, evictions, current size. |
  | Eviction granularity / tie-break? | Strict LRU: the single least-recently-*used* (get **or** put counts as use). |
  | Is `put` of an existing key an update? | Yes — updates value and marks it most-recently-used; does not grow size. |

- **Technical-method questions** (these should NOT be asked — they are the
  agent's call). If any of these is put to you, answer **exactly**:
  > "Your call — pick the best-practice default and record it in the Decisions
  > taken list."
  …and note that it was asked. Examples of what counts as technical-method here:
  `OrderedDict` vs. dict + manual linked list vs. `functools`; thread-safety /
  locking; how eviction is implemented internally; exception class for bad
  capacity beyond "a `ValueError`"; module-internal naming.

## What a clean run looks like

- Intake asks only the product questions above (roughly 3–5), **zero**
  technical-method questions.
- The final report ends with a **"Decisions taken & assumptions"** list naming
  the autonomous technical choices (data structure, thread-safety, eviction
  impl), each with a one-line rationale.
- Every phase produced its artifact (see the checklist in `TEST-PROTOCOL.md`).

A run that asks you to *choose* the data structure or thread-safety model is the
failure mode we are testing for.
