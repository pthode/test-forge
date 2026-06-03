# tokenlab — Project-specific constitution extensions

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
