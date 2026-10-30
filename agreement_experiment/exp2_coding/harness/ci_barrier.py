#!/usr/bin/env python3
"""Harness 'CI with barrier' (Stop hook). Exit 2 blocks.

An agent may finish only when BOTH agents have asked to finish on their current files
(a 'ready' mark with the hash of both files) and the merged code passes the public example.
Like a two-phase commit: each side prepares (ready); the run commits only if both are ready
on the same versions and the check passes. A file change after 'ready' invalidates it.
Blocks at most MAX_BLOCKS times per agent so a run cannot loop forever.
"""
import hashlib, json, os, sys

sys.path.insert(0, os.environ["EVAL_DIR"])
from run_hidden import evaluate  # noqa: E402

MAX_BLOCKS = 10
EV = os.environ["HARNESS_EVENTS"]
ME = os.environ["AGENT_ID"]
OTHER = "agent2" if ME == "agent1" else "agent1"
SHARED = os.path.dirname(EV)
P, I = os.environ["PRICING_FILE"], os.environ["INVOICE_FILE"]


def h():
    m = hashlib.sha256()
    for p in (P, I):
        m.update(open(p, "rb").read() if os.path.exists(p) else b"-")
    return m.hexdigest()[:16]


def n_blocks():
    return sum(1 for l in open(EV) if json.loads(l)["agent"] == ME) if os.path.exists(EV) else 0


def block(msg):
    with open(EV, "a") as f:
        f.write(json.dumps({"agent": ME, "block": msg[:200]}) + "\n")
    print(msg, file=sys.stderr)
    sys.exit(2)


def main():
    json.load(sys.stdin)
    if n_blocks() >= MAX_BLOCKS:
        return
    cur = h()
    open(os.path.join(SHARED, f"ready_{ME}"), "w").write(cur)
    r = evaluate(P, I, example_only=True)
    if r["passed"] < r["total"]:
        c = (r["cases"] or [{}])[0]
        detail = r["error"][-400:] if r["error"] else f"expected:\n{c.get('want')}\ngot:\n{c.get('got')}"
        block("[CI] Integration check failed when combining the CURRENT pricing.py (agent1) and invoice.py (agent2) "
              f"on the example order:\n{detail}\nCoordinate with your teammate, fix your part, then try to finish again.")
    other_ready = os.path.join(SHARED, f"ready_{OTHER}")
    if not os.path.exists(other_ready) or open(other_ready).read() != cur:
        block(f"[CI] The integration check passes now, but you cannot finish until {OTHER} has also finished on "
              "these exact versions of both files. Tell your teammate, wait (python3 $TOOLS/msg.py wait 60), "
              "and try to finish again. Do not change your file unless the check fails.")


if __name__ == "__main__":
    main()
