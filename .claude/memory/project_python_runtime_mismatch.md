---
name: project-python-runtime-mismatch
description: Local dev runtime is Python 3.11.9 but CONSTITUTION §1 pins 3.12; CI runs on 3.12
metadata:
  type: project
---

The local development machine runs **Python 3.11.9**, but `CONSTITUTION.md` §1 pins the project to **Python 3.12**. The `parse-duration` stdlib code behaves identically on both, so local `pytest` (82 tests) passes on 3.11.9, but the constitutional runtime is 3.12.

**Why:** Discovered during the first `/autopilot` run (parse-duration). release-engineer correctly insisted "green in CI" (§9 DoD) be verified on 3.12, not the local 3.11.9.

**How to apply:** The authoritative test signal is CI (`.github/workflows/ci.yml`, runs on 3.12), not local pytest. When a feature uses a 3.12-only stdlib/syntax feature, local runs on 3.11.9 may give a false pass/fail — trust CI. Consider installing 3.12 locally to close the gap.
