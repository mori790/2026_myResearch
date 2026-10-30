#!/usr/bin/env python3
"""Evaluate all trials in runs/ and print a summary table (also writes results.csv)."""
import csv, glob, json, os, sys

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(ROOT, "tools"))
from check_output import check, norm  # noqa: E402


def jl(path):
    return [json.loads(l) for l in open(path)] if os.path.exists(path) else []


def eval_trial(tdir):
    meta = json.load(open(os.path.join(tdir, "trial.json")))
    row = dict(meta)
    reps, cost, turns, errors = {}, 0.0, 0, []
    for aid in ("agent1", "agent2"):
        out = os.path.join(tdir, aid, "out", "report.json")
        ok, msg = check(out)
        row[f"{aid}_valid"] = ok
        row[f"{aid}_msg"] = msg
        try:
            reps[aid] = json.load(open(out))
        except Exception:  # noqa: BLE001
            reps[aid] = None
        try:
            res = json.load(open(os.path.join(tdir, aid, "result.json")))
            cost += res.get("total_cost_usd", 0) or 0
            turns += res.get("num_turns", 0) or 0
            if res.get("is_error"):
                errors.append(f"{aid}:{res.get('subtype')}")
        except Exception as e:  # noqa: BLE001
            errors.append(f"{aid}:no-result({e.__class__.__name__})")
        row[f"{aid}_skill_used"] = False
        sp = os.path.join(tdir, aid, "stream.jsonl")
        if os.path.exists(sp):
            for line in open(sp):
                if '"name":"Skill"' in line.replace(" ", ""):
                    row[f"{aid}_skill_used"] = True
    r1, r2 = reps["agent1"], reps["agent2"]
    same_rule = bool(r1 and r2 and norm(r1["rule"]) == norm(r2["rule"]))
    same_excl = bool(r1 and r2 and sorted(r1.get("excluded_ids", [])) == sorted(r2.get("excluded_ids", [])))
    row["consistent"] = same_rule and same_excl
    row["success"] = row["consistent"] and row["agent1_valid"] and row["agent2_valid"]
    row["rules"] = f"{r1 and r1.get('rule')} | {r2 and r2.get('rule')}"
    shared = os.path.join(tdir, "shared")
    row["messages"] = len(jl(os.path.join(shared, "messages.jsonl")))
    log = jl(os.path.join(shared, "agreement_log.jsonl"))
    row["agree_ops"] = sum(1 for e in log if e["kind"] != "init")
    row["committed"] = any(e["kind"] == "commit" for e in log)
    row["harness_blocks"] = len(jl(os.path.join(shared, "harness_events.jsonl")))
    row["cost_usd"] = round(cost, 3)
    row["turns"] = turns
    row["errors"] = ";".join(errors)
    return row


def main():
    rows = [eval_trial(d) for d in sorted(glob.glob(os.path.join(ROOT, "runs", "*")))
            if os.path.exists(os.path.join(d, "trial.json"))]
    if not rows:
        print("no trials"); return
    keys = list(rows[0].keys())
    with open(os.path.join(ROOT, "results.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, keys); w.writeheader(); w.writerows(rows)
    for r in rows:
        print(f"{r['cond']:8} r{r['rep']}  success={str(r['success']):5} consistent={str(r['consistent']):5} "
              f"valid={r['agent1_valid']!s:5}/{r['agent2_valid']!s:5} msgs={r['messages']:2} agree={r['agree_ops']:2} "
              f"blocks={r['harness_blocks']:2} skill={int(r.get('agent1_skill_used',0))+int(r.get('agent2_skill_used',0))} cost=${r['cost_usd']:.2f} wall={r['wall_s']}s {r['errors']}")
        print(f"          rules: {r['rules']}")
    print("\nby condition:")
    for c in ("base", "skill", "harness", "both"):
        rs = [r for r in rows if r["cond"] == c]
        if rs:
            n = len(rs)
            print(f"  {c:8} n={n}  success={sum(r['success'] for r in rs)}/{n}  "
                  f"consistent={sum(r['consistent'] for r in rs)}/{n}  "
                  f"mean_cost=${sum(r['cost_usd'] for r in rs)/n:.2f}  mean_wall={sum(r['wall_s'] for r in rs)/n:.0f}s")


if __name__ == "__main__":
    main()
