import json, glob, os, time
from collections import Counter
PROJECTS = os.path.expanduser("~/.claude/projects")
CUTOFF = time.time() - 6*3600
cands = {}
# PATH FIX ONLY: transcripts live at PROJECTS/<proj>/<session-uuid>/subagents/agent-*.jsonl
for jl in glob.glob(os.path.join(PROJECTS, "*", "*", "subagents", "agent-*.jsonl")):
    proj = os.path.dirname(os.path.dirname(jl))
    cands[proj] = max(cands.get(proj, 0), os.path.getmtime(jl))
if not cands:
    print("No subagent transcripts found."); raise SystemExit
proj = max(cands, key=cands.get)
print("Project session dir:", proj)
def usages(path):
    out=[]
    for line in open(path, encoding="utf-8"):
        if not line.strip(): continue
        try: o=json.loads(line)
        except: continue
        m=o.get("message"); u=m.get("usage") if isinstance(m,dict) else None
        if u: out.append(u)
    return out
def agg(us):
    cold=us[0].get("cache_creation_input_tokens",0) if us else 0
    cc=sum(u.get("cache_creation_input_tokens",0) for u in us)
    cr=sum(u.get("cache_read_input_tokens",0) for u in us)
    inp=sum(u.get("input_tokens",0) for u in us)
    out=sum(u.get("output_tokens",0) for u in us)
    cost=cc*1.25+cr*0.1+inp+out*5
    return cold,cc,cr,inp,out,cost,len(us)
rows=[]
for jl in glob.glob(os.path.join(proj,"subagents","agent-*.jsonl")):
    if os.path.getmtime(jl) < CUTOFF: continue
    at="?"; meta=jl.replace(".jsonl",".meta.json")
    if os.path.exists(meta):
        try: at=json.load(open(meta,encoding="utf-8")).get("agentType","?")
        except: pass
    cold,cc,cr,inp,out,cost,turns=agg(usages(jl))
    rows.append((at,turns,cold,cc,cr,out,cost))
orch=None
# PATH FIX ONLY: orchestrator jsonl is the sibling file PROJECTS/<proj>/<session-uuid>.jsonl
tops=glob.glob(os.path.join(os.path.dirname(proj),"*.jsonl"))
if tops:
    top=max(tops,key=os.path.getmtime)
    cold,cc,cr,inp,out,cost,turns=agg(usages(top))
    orch=("ORCHESTRATOR",turns,cold,cc,cr,out,cost)
print("\n%-20s %5s %9s %9s %9s %8s %11s %7s"%("agent","turns","cold_cc","sum_cc","sum_cr","out","cost_wt","cold%"))
def line(r):
    at,turns,cold,cc,cr,out,cost=r
    cs=(cold*1.25)/cost*100 if cost else 0
    print("%-20s %5d %9d %9d %9d %8d %11.0f %6.1f"%(at,turns,cold,cc,cr,out,cost,cs))
if orch: line(orch)
for r in sorted(rows): line(r)
print("\nInvocations per agent type:", dict(Counter(r[0] for r in rows)))
tot_cost=sum(r[6] for r in rows)+(orch[6] if orch else 0)
tot_out=sum(r[5] for r in rows)+(orch[5] if orch else 0)
print("TOTAL subagents:", len(rows))
print("TOTAL cost-weighted input-equiv tokens (orchestrator + subagents):", round(tot_cost))
print("TOTAL output tokens:", tot_out)
