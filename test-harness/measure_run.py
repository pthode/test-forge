"""measure_run.py — efficiency/interruption profile of one autopilot run.

Extends the earlier `measure_tokens_fixed.py` (token cost per agent) with the
three things we actually need to compare forge versions:

  - wall-clock elapsed  (min..max transcript timestamp)
  - convergence proxy   (# qa-reviewer invocations == Phase 3 rounds;
                         # release-engineer invocations == Phase 4 attempts)
  - a tagged JSON dump  (run-<forge-version>-<session>.json) so two runs diff

It deliberately does NOT try to count `AskUserQuestion` calls: those are not
reliably serialized in the transcript (questions can be asked as plain chat),
so the over-asking signal is read by hand from the requirements ticket §13/§14
instead — see TEST-PROTOCOL.md. This script measures cost and time only;
correctness and over-asking are human-judged against the committed artifacts.

Usage:
  python test-harness/measure_run.py            # analyse latest session, write JSON
  python test-harness/measure_run.py --compare run-A.json run-B.json
"""

import json, glob, os, sys, time
from collections import Counter
from datetime import datetime

PROJECTS = os.path.expanduser("~/.claude/projects")
WINDOW_HOURS = 12                       # only count subagent files from the last run
CUTOFF = time.time() - WINDOW_HOURS * 3600

# Cost weighting identical to the earlier token measurement, so numbers stay
# comparable across the two scripts: cache-create 1.25x, cache-read 0.1x,
# fresh input 1x, output 5x. This is an input-equivalent unit, not USD.
def cost_of(u):
    return (u.get("cache_creation_input_tokens", 0) * 1.25
            + u.get("cache_read_input_tokens", 0) * 0.1
            + u.get("input_tokens", 0)
            + u.get("output_tokens", 0) * 5)


def parse_ts(o):
    ts = o.get("timestamp")
    if not ts:
        return None
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except Exception:
        return None


def scan(path):
    """Return (usages, min_ts, max_ts) for one jsonl transcript."""
    usages, lo, hi = [], None, None
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                o = json.loads(line)
            except Exception:
                continue
            t = parse_ts(o)
            if t:
                lo = t if lo is None or t < lo else lo
                hi = t if hi is None or t > hi else hi
            m = o.get("message")
            u = m.get("usage") if isinstance(m, dict) else None
            if u:
                usages.append(u)
    return usages, lo, hi


def agg(usages):
    cold = usages[0].get("cache_creation_input_tokens", 0) if usages else 0
    cc = sum(u.get("cache_creation_input_tokens", 0) for u in usages)
    cr = sum(u.get("cache_read_input_tokens", 0) for u in usages)
    out = sum(u.get("output_tokens", 0) for u in usages)
    cost = sum(cost_of(u) for u in usages)
    return cold, cc, cr, out, cost, len(usages)


def latest_session_dir():
    cands = {}
    for jl in glob.glob(os.path.join(PROJECTS, "*", "*", "subagents", "agent-*.jsonl")):
        proj = os.path.dirname(os.path.dirname(jl))      # .../<proj>/<session-uuid>
        cands[proj] = max(cands.get(proj, 0), os.path.getmtime(jl))
    if not cands:
        sys.exit("No subagent transcripts found under " + PROJECTS)
    return max(cands, key=cands.get)


def forge_version():
    try:
        with open(".forge-version", encoding="utf-8") as fh:
            return fh.read().strip()
    except OSError:
        return "unknown"


def analyse():
    session = latest_session_dir()
    print("Session dir:", session)

    lo = hi = None
    rows = []
    for jl in glob.glob(os.path.join(session, "subagents", "agent-*.jsonl")):
        if os.path.getmtime(jl) < CUTOFF:
            continue
        at = "?"
        meta = jl.replace(".jsonl", ".meta.json")
        if os.path.exists(meta):
            try:
                at = json.load(open(meta, encoding="utf-8")).get("agentType", "?")
            except Exception:
                pass
        us, a, b = scan(jl)
        cold, cc, cr, out, cost, turns = agg(us)
        rows.append((at, turns, cold, cc, cr, out, cost))
        if a: lo = a if lo is None or a < lo else lo
        if b: hi = b if hi is None or b > hi else hi

    # orchestrator transcript is the sibling <session-uuid>.jsonl
    orch = None
    for top in glob.glob(os.path.join(os.path.dirname(session), "*.jsonl")):
        if os.path.basename(session) in top:
            us, a, b = scan(top)
            cold, cc, cr, out, cost, turns = agg(us)
            orch = ("ORCHESTRATOR", turns, cold, cc, cr, out, cost)
            if a: lo = a if lo is None or a < lo else lo
            if b: hi = b if hi is None or b > hi else hi
            break

    counts = Counter(r[0] for r in rows)
    total_cost = sum(r[6] for r in rows) + (orch[6] if orch else 0)
    total_out = sum(r[5] for r in rows) + (orch[5] if orch else 0)
    wall = (hi - lo).total_seconds() if lo and hi else None

    # ---- print human table ----
    hdr = "%-20s %5s %9s %9s %9s %8s %11s"
    print("\n" + hdr % ("agent", "turns", "cold_cc", "sum_cc", "sum_cr", "out", "cost_wt"))
    def line(r):
        at, turns, cold, cc, cr, out, cost = r
        print("%-20s %5d %9d %9d %9d %8d %11.0f" % (at, turns, cold, cc, cr, out, cost))
    if orch: line(orch)
    for r in sorted(rows): line(r)

    print("\nInvocations per agent type:", dict(counts))
    print("Convergence proxy  — qa-reviewer rounds   :", counts.get("qa-reviewer", 0))
    print("Release proxy      — release-engineer runs:", counts.get("release-engineer", 0))
    print("Subagents total                           :", len(rows))
    print("Wall-clock (incl. human think-time)       :",
          ("%.1f min" % (wall / 60)) if wall else "n/a")
    print("Cost-weighted input-equiv tokens (total)  :", round(total_cost))
    print("Output tokens (total)                     :", total_out)

    # ---- dump JSON for diffing ----
    ver = forge_version()
    summary = {
        "forge_version": ver,
        "session": os.path.basename(session),
        "wall_clock_seconds": round(wall) if wall else None,
        "qa_reviewer_rounds": counts.get("qa-reviewer", 0),
        "release_engineer_runs": counts.get("release-engineer", 0),
        "subagents_total": len(rows),
        "invocations_per_type": dict(counts),
        "cost_weighted_input_equiv": round(total_cost),
        "output_tokens": total_out,
    }
    out_name = "run-%s-%s.json" % (ver, os.path.basename(session)[:8])
    with open(out_name, "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2)
    print("\nWrote", out_name)


def compare(a_path, b_path):
    a = json.load(open(a_path, encoding="utf-8"))
    b = json.load(open(b_path, encoding="utf-8"))
    print("%-32s %14s %14s %12s" % ("metric", a.get("forge_version", "A"),
                                    b.get("forge_version", "B"), "delta"))
    for k in ("wall_clock_seconds", "qa_reviewer_rounds", "release_engineer_runs",
              "subagents_total", "cost_weighted_input_equiv", "output_tokens"):
        av, bv = a.get(k), b.get(k)
        if isinstance(av, (int, float)) and isinstance(bv, (int, float)):
            d = bv - av
            pct = (" (%+.0f%%)" % (100 * d / av)) if av else ""
            print("%-32s %14s %14s %12s" % (k, av, bv, ("%+d%s" % (d, pct))))
        else:
            print("%-32s %14s %14s %12s" % (k, av, bv, "-"))
    print("\nNOTE: a single run is one sample, not a measurement. Differences"
          " under ~15% are within run-to-run variance; run the fixture 2-3x"
          " per version before trusting a token/time delta. The over-asking"
          " signal (ticket §13 vs §14) is more robust and is judged by hand.")


if __name__ == "__main__":
    if len(sys.argv) >= 4 and sys.argv[1] == "--compare":
        compare(sys.argv[2], sys.argv[3])
    else:
        analyse()
