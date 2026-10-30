"""Conf(o, d): output JSON's excluded ids must equal the rule's reference result."""
import json, os, sys
sys.path.insert(0, os.path.dirname(__file__))
from rules import load, excluded
d=json.load(open(os.environ["DECISION_FILE"]))
o=json.load(open(os.environ["OUTPUT_PATH"]))
want=excluded(load(os.path.join(os.path.dirname(__file__),"data.csv")), d)
got=sorted(o["excluded_ids"])
if got==want: print(f"n_excluded={len(got)} matches rule {d}"); sys.exit(0)
print(f"mismatch: expected {len(want)} excluded, got {len(got)}; extra={sorted(set(got)-set(want))} missing={sorted(set(want)-set(got))}"); sys.exit(1)
