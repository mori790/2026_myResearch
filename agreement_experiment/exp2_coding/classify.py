#!/usr/bin/env python3
"""Classify failed trials: coordination (interface mismatch) vs individual (one side's own bug)."""
import csv, json, os, sys, collections
ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(ROOT, "eval"))
from run_hidden import evaluate

import re
def _zero_fmt(text):
    """Normalise how a zero amount is printed ($0 / $0.00 / -$0.00): an individual formatting slip."""
    return re.sub(r"-?\$0(\.00)?(?=$|\s)", "$0.00", text, flags=re.M)

def classify(t):
    r = evaluate(f"{t}/agent1/repo/pricing.py", f"{t}/agent2/repo/invoice.py")
    if r["passed"] == r["total"]:
        return "ok"
    if r["error"] or "NotImplementedError" in open(f"{t}/agent1/repo/pricing.py").read() \
            or "NotImplementedError" in open(f"{t}/agent2/repo/invoice.py").read():
        return "not_delivered"
    kinds = set()
    for c in r["cases"]:
        if c["ok"]:
            continue
        g, w = c["got"], c["want"]
        if "EXCEPTION" in g or "NoneType" in g:
            kinds.add("coordination:interface")
        elif _zero_fmt(g) == _zero_fmt(w):
            kinds.add("individual:format")
        elif c["bypass"]:
            kinds.add("bypass")
        else:
            kinds.add("coordination:values")
    return "+".join(sorted(kinds))

rows = list(csv.DictReader(open(os.path.join(ROOT, "results.csv"))))
out = collections.defaultdict(collections.Counter)
for r in rows:
    k = classify(os.path.join(ROOT, "runs", f"{r['cond']}_r{r['rep']}"))
    out[r["cond"]][k] += 1
    if k != "ok":
        print(f"{r['cond']:10} r{r['rep']:>2}: {k}")
print()
for c in ("base", "tool", "inline", "skill", "gate", "ci", "ci_barrier", "skill_ci"):
    print(f"{c:10} {dict(out[c])}")
