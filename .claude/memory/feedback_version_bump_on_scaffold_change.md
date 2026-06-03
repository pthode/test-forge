---
name: feedback_version_bump_on_scaffold_change
description: Bump .forge-version and add an UPGRADING.md entry whenever scaffold files change
metadata:
  type: feedback
---

Any change to forge-owned scaffold files (`.claude/agents/`, `.claude/commands/`, `.claude/templates/`, `CONSTITUTION.template.md`) requires two housekeeping steps before the work is complete:

1. Bump `.forge-version` — patch for fixes/tweaks, minor for new features, major for breaking changes.
2. Add a version entry to `UPGRADING.md` following the established format: version-prefixed `###` subsection headings (`### X.Y.Z — What changed`, `### X.Y.Z — Forge-owned file changes`, `### X.Y.Z — Manual steps for existing CONSTITUTION.md`, `### X.Y.Z — Verify`).

**Why:** `forge-update` uses `.forge-version` to compare project vs. upstream and to identify which `UPGRADING.md` entries apply. Without these steps, downstream projects cannot detect that an upgrade is available or know what manual migration steps to take for their `CONSTITUTION.md`.

**How to apply:** Treat `.forge-version` + `UPGRADING.md` as part of the changeset for any scaffold edit — same commit, not a follow-up.
