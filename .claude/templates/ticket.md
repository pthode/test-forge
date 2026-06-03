# <feature> — Requirements Ticket

> Locked on <YYYY-MM-DD> by requirements-intake. Reopening requires a new autopilot run.

## 1. One-line summary
<one sentence the user could read>

## 2. Context
<2-4 sentences: why this exists, what triggered it, what it replaces or augments>

## 3. In scope
- <bullet>
- ...

## 4. Out of scope (explicit non-goals)
- <bullet — things downstream agents must NOT build>
- ...

## 5. Actors and triggers
- Who initiates this? Under what conditions?

## 6. Inputs
- Shape, source, validation rules.

## 7. Outputs
- Shape, destination, format.

## 8. Persistence
- What's stored, where, for how long. "None" is a valid answer.

## 9. External dependencies
- Services, APIs, libraries the system must talk to. "None" is a valid answer.

## 10. Failure behavior
- What happens when each external dependency fails?
- What's recoverable, what's fatal?

## 11. Non-functional constraints
- Performance, security, accessibility, regulatory. Reference constitution sections where applicable.

## 12. Success criteria
- Bulleted, testable conditions. test-engineer will write tests against these.

## 13. Answered questions (intake transcript)
| # | Question | Answer |
|---|----------|--------|
| Q1 | … | … |

## 14. Inferred assumptions (NOT confirmed by user)
- <each item flagged with `(inferred)` in the ticket body>
- spec-architect MAY override these if they discover a conflict, but MUST cite the conflict in §9 of the resulting SDD.
