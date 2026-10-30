#!/usr/bin/env python3
"""Evaluate experiment 2 trials: hidden integration tests + process metrics."""
import csv, glob, json, os, sys

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(ROOT, "eval"))
from run_hidden import evaluate  # noqa: E402


def jl(p):
    return [json.loads(l) for l in open(p)] if os.path.exists(p) else []


def tool_uses(stream):
    names = []
    for ev in jl(stream):
        if ev.get("type") == "assistant":
            for c in ev.get("message", {}).get("content", []):
                if c.get("type") == "tool_use":
                    names.append((c["name"], json.dumps(c.get("input", {}))[:200]))
    return names


def eval_trial(t):
    meta = json.load(open(os.path.join(t, "trial.json")))
    r = evaluate(os.path.join(t, "agent1", "repo", "pricing.py"), os.path.join(t, "agent2", "repo", "invoice.py"))
    row = dict(meta, passed=r["passed"], total=r["total"], success=r["passed"] == r["total"],
               bypass=any(c["bypass"] for c in r["cases"]), error=r["error"][:120].replace("\n", " "))
    cost, turns, skill, agree = 0.0, 0, 0, 0
    for aid in ("agent1", "agent2"):
        res = json.load(open(os.path.join(t, aid, "result.json")))
        cost += res.get("total_cost_usd") or 0
        turns += res.get("num_turns") or 0
        uses = tool_uses(os.path.join(t, aid, "stream.jsonl"))
        skill += any(n == "Skill" for n, _ in uses)
        agree += sum(1 for n, i in uses if n == "Bash" and "agree.py" in i)
    sh = os.path.join(t, "shared")
    log = jl(os.path.join(sh, "agreement_log.jsonl"))
    row.update(cost_usd=round(cost, 3), turns=turns, skill_invoked=skill, agree_calls=agree,
               commits=sum(1 for e in log if e["kind"] == "commit"),
               messages=len(jl(os.path.join(sh, "messages.jsonl"))),
               ci_blocks=len(jl(os.path.join(sh, "harness_events.jsonl"))))
    return row


def main():
    rows = [eval_trial(d) for d in sorted(glob.glob(os.path.join(ROOT, "runs", "*")))
            if os.path.exists(os.path.join(d, "trial.json"))]
    if not rows:
        print("no trials"); return
    with open(os.path.join(ROOT, "results.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    for r in rows:
        print(f"{r['cond']:9} r{r['rep']} pass={r['passed']}/{r['total']} bypass={int(r['bypass'])} msgs={r['messages']:2} "
              f"skill={r['skill_invoked']} agree={r['agree_calls']:2} commits={r['commits']} ci_blocks={r['ci_blocks']} "
              f"cost=${r['cost_usd']:.2f} wall={r['wall_s']:.0f}s {r['error'][:60]}")
    print("\nby condition:")
    for c in ("base", "tool", "inline", "skill", "gate", "ci", "ci_barrier", "skill_ci"):
        rs = [r for r in rows if r["cond"] == c]
        if rs:
            n = len(rs)
            print(f"  {c:9} n={n} success={sum(r['success'] for r in rs)}/{n} "
                  f"mean_pass={sum(r['passed'] for r in rs)/n:.1f}/{rs[0]['total']} "
                  f"mean_cost=${sum(r['cost_usd'] for r in rs)/n:.2f} mean_wall={sum(r['wall_s'] for r in rs)/n:.0f}s")


if __name__ == "__main__":
    main()
