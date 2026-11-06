#!/usr/bin/env python3
"""Score every run in runs/: hidden tests per group, plus how the agents used the agreement tool.
Writes results.csv and prints a per-condition summary."""
import csv, glob, json, os, sys
from collections import defaultdict
ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(ROOT, "eval"))
sys.path.insert(0, os.path.join(ROOT, "tools"))
from run_hidden import evaluate  # noqa: E402
import agree  # noqa: E402

GROUPS = ["example", "basic", "unknown", "discount", "tax", "exempt", "unknown_customer", "combined"]
AGENTS = ("agent1", "agent2", "agent3")


def tool_calls(stream):
    n = 0
    for line in open(stream):
        try:
            ev = json.loads(line)
        except json.JSONDecodeError:
            continue
        if ev.get("type") != "assistant":
            continue
        for c in ev["message"].get("content", []):
            if c.get("type") == "tool_use" and "agree.py" in json.dumps(c.get("input", {})):
                n += 1
    return n


rows = []
for tdir in sorted(glob.glob(os.path.join(ROOT, "runs", "*_r*"))):
    if not os.path.exists(os.path.join(tdir, "trial.json")):
        continue
    t = json.load(open(os.path.join(tdir, "trial.json")))
    r = evaluate(os.path.join(tdir, "agent1", "repo", "pricing.py"), os.path.join(tdir, "agent2", "repo", "tax.py"),
                 os.path.join(tdir, "agent3", "repo", "invoice.py"))
    by = defaultdict(lambda: [0, 0])
    for c in r["cases"]:
        by[c["group"]][0] += c["ok"]
        by[c["group"]][1] += 1
    entries = agree._read(os.path.join(tdir, "shared", "agreement_log.jsonl"))
    _, topics = agree.state(entries)
    committed = [n for n, x in topics.items() if n and x["committed"]]
    msgs = os.path.join(tdir, "shared", "messages.jsonl")
    hev = os.path.join(tdir, "shared", "harness_events.jsonl")
    res = [json.load(open(os.path.join(tdir, a, "result.json"))) for a in AGENTS]
    row = {"cond": t["cond"], "rep": t["rep"], "wall_s": t["wall_s"], "passed": r["passed"], "total": r["total"],
           "success": r["passed"] == r["total"], "error": r["error"][:120].replace("\n", " "),
           "agree_calls": sum(tool_calls(os.path.join(tdir, a, "stream.jsonl")) for a in AGENTS),
           "topics": len([n for n in topics if n]), "committed": len(committed), "committed_topics": "|".join(committed),
           "messages": sum(1 for _ in open(msgs)) if os.path.exists(msgs) else 0,
           "gate_blocks": sum(1 for _ in open(hev)) if os.path.exists(hev) else 0,
           "cost_usd": round(sum(x.get("total_cost_usd", 0) or 0 for x in res), 3)}
    for g in GROUPS:
        row["g_" + g] = f"{by[g][0]}/{by[g][1]}" if by[g][1] else "0/0"
    rows.append(row)

if rows:
    with open(os.path.join(ROOT, "results.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
for cond in ("baseline", "advisory", "enforced"):
    rs = [x for x in rows if x["cond"] == cond]
    if not rs:
        continue
    print(f"{cond:9s} n={len(rs)} success={sum(x['success'] for x in rs)} "
          f"committed>0={sum(x['committed'] > 0 for x in rs)} mean_wall={sum(x['wall_s'] for x in rs)/len(rs):.0f}s")
    for x in rs:
        print("   r%-2d %2d/%-2d %s commits=%d blocks=%d %s" % (
            x["rep"], x["passed"], x["total"], " ".join(f"{g[:4]}={x['g_'+g]}" for g in GROUPS[1:]),
            x["committed"], x["gate_blocks"], x["error"][:60]))
