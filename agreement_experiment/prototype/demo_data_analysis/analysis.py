"""An 'agent output': chapter analysis using some exclusion rule."""
import json, sys, statistics
from rules import load, excluded
rule=json.loads(sys.argv[1]); out=sys.argv[2]
rows=load(); ex=excluded(rows, rule)
kept=[r["rt"] for r in rows if r["id"] not in ex]
json.dump({"excluded_ids":ex,"n":len(kept),"mean_rt":round(statistics.mean(kept),1)}, open(out,"w"))
print(out, "n=",len(kept),"mean=",round(statistics.mean(kept),1))
