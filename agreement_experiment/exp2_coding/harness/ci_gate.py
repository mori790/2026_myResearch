#!/usr/bin/env python3
"""Harness for experiment 2: a CI gate on Stop (Claude Code Stop hook). Exit 2 blocks.

When an agent tries to finish, the harness merges BOTH agents' current files
(agent1's pricing.py + agent2's invoice.py) and runs the public example from the
task description. If it fails, finishing is blocked and the diff is shown.
Blocks at most MAX_BLOCKS times per agent so a run cannot loop forever.
"""
import json, os, sys

sys.path.insert(0, os.environ["EVAL_DIR"])
from run_hidden import evaluate  # noqa: E402

MAX_BLOCKS = 4
EVENTS = os.environ["HARNESS_EVENTS"]
ME = os.environ["AGENT_ID"]


def n_blocks():
    if not os.path.exists(EVENTS):
        return 0
    return sum(1 for l in open(EVENTS) if json.loads(l)["agent"] == ME)


def block(msg):
    with open(EVENTS, "a") as f:
        f.write(json.dumps({"agent": ME, "block": msg[:300]}) + "\n")
    print(msg, file=sys.stderr)
    sys.exit(2)


def main():
    json.load(sys.stdin)
    if n_blocks() >= MAX_BLOCKS:
        return
    pricing, invoice = os.environ["PRICING_FILE"], os.environ["INVOICE_FILE"]
    missing = [p for p in (pricing, invoice) if not os.path.exists(p) or "NotImplementedError" in open(p).read()]
    if missing:
        who = "your teammate's" if all(ME not in p for p in missing) else "your"
        block(f"[CI] Cannot finish yet: {who} module is not implemented ({', '.join(os.path.basename(m) for m in missing)}). "
              f"Check messages with your teammate (msg.py read / wait 60) and try again.")
    r = evaluate(pricing, invoice, example_only=True)
    if r["passed"] < r["total"]:
        if r["error"]:
            detail = r["error"][-400:]
        else:
            c = r["cases"][0]
            detail = f"expected:\n{c['want']}\ngot:\n{c['got']}" + ("\n(invoice.py did not call pricing.price_of)" if c["bypass"] else "")
        block("[CI] Integration check failed when combining pricing.py (agent1) and invoice.py (agent2) "
              f"on the example order {{'customer': 'C1', 'lines': [['A', 2], ['Z', 1]]}}:\n{detail}\n"
              "Coordinate with your teammate and fix your part.")


if __name__ == "__main__":
    main()
