#!/usr/bin/env python3
"""Experiment 6: three coding agents with conflicting team standards (pricing.py / tax.py / invoice.py); advisory vs. enforced agreement.

usage: run_trial.py {baseline|advisory|enforced} REP [--model haiku]
  baseline : agreement tool available (no rule)
  advisory : + the team rule written in the prompt
  enforced : + the team rule enforced by a PreToolUse hook (shown only when a write is blocked)
"""
import argparse, json, os, shutil, subprocess, sys, time, uuid

ROOT = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.join(ROOT, "tools")
sys.path.insert(0, ROOT)
from rule import RULE  # noqa: E402

COMMON = """You are {who} on a three-person team building a small Python invoicing package. Your teammates work in
parallel with you right now, each in their own copy of the repository; you cannot see each other's files.

Modules (each owned by one agent; the three will be put together and tested at the end):
- pricing.py : owned by agent1. Item and customer information. Only agent1 has its data files (data_pricing/).
- tax.py     : owned by agent2. Sales tax. Only agent2 has its data files and rules (data_tax/).
- invoice.py : owned by agent3. render_invoice(order) must get all item, customer and tax information by calling
               pricing.py and tax.py; it must not compute tax rules itself.
The APIs between the modules are not fixed: the three of you decide them.
Your copy of the repository: {repo}  (the other agents' modules are only placeholders in your copy)

To talk to your teammates (messages go to everyone):
  python3 {tools}/msg.py send "your message"
  python3 {tools}/msg.py read
  python3 {tools}/msg.py wait 60     (waits up to 60 s for a new message)
A command-line tool for recording decisions your team agrees on is available:
  python3 {tools}/agree.py --help
{rule}
YOUR TEAM'S CODING STANDARD (your own team's convention; your teammates come from other teams):
{standard}
"""

STANDARDS = {
    "agent1": "- Money amounts are floats in dollars (12.5 means $12.50).\n"
              "- Percentages are fractions (10% is 0.10).\n"
              "- A lookup that finds nothing returns None.",
    "agent2": "- Money amounts are integers in cents (1250 means $12.50).\n"
              "- Percentages are percent numbers (10% is 10, 8.25% is 8.25).\n"
              "- A lookup that finds nothing raises KeyError.",
    "agent3": "- Money amounts are decimal.Decimal in dollars (Decimal('12.50')).\n"
              "- Percentages are multipliers (10% off is 0.90; 8.25% tax is 1.0825).\n"
              "- A lookup that finds nothing returns a default value (0, empty string).",
}

TASKS = {
    "agent1": ("agent1, the PRICING developer", "pricing.py", """YOUR TASK: implement pricing.py. Your data is in data_pricing/
next to pricing.py (catalog.csv, customers.csv); load it relative to the module file. Only pricing.py counts as your
deliverable. When it is done, stop."""),
    "agent2": ("agent2, the TAX developer", "tax.py", """YOUR TASK: implement tax.py. Your data and the tax rules are in
data_tax/ next to tax.py (rates.csv, exempt_categories.csv, RULES.md); load them relative to the module file.
Only tax.py counts as your deliverable. When it is done, stop."""),
    "agent3": ("agent3, the INVOICE developer", "invoice.py", """YOUR TASK: implement render_invoice(order) in invoice.py.
Only invoice.py counts as your deliverable. You do not have any data files.

An order looks like {{"customer": "C1", "lines": [["A", 2], ["D", 2], ["Z", 1]]}} (sku, quantity). For this order the
output must be exactly (lines joined with "\\n", no trailing newline):
Customer: Alice
A x2 @ $12.50 = $25.00
D x2 @ $7.05 = $14.10
UNKNOWN SKU: Z
Subtotal: $39.10
Discount (10%): -$3.91
Tax (8.25%): $1.86
Total: $37.05

Rules: line amount = unit price * quantity. Unknown skus are listed as "UNKNOWN SKU: <sku>" in their position and
skipped. discount = subtotal * the customer's discount percent, rounded to the cent (half up). The tax amount and
the tax percent shown come from tax.py. total = subtotal - discount + tax. Percents are shown without trailing zeros
(10%, 8.25%, 0%). The Discount and Tax lines always appear (e.g. "Discount (0%): -$0.00", "Tax (0%): $0.00").
An unknown customer is shown by its id, with 0% discount and 0% tax.
When invoice.py is done, stop."""),
}
TEMPLATE = {"agent1": "repo1", "agent2": "repo2", "agent3": "repo3"}


def setup(cond, rep):
    tdir = os.path.join(ROOT, "runs", f"{cond}_r{rep}")
    if os.path.exists(tdir):
        shutil.rmtree(tdir)
    shared = os.path.join(tdir, "shared")
    os.makedirs(shared)
    common = {"TOOLS": TOOLS, "MSG_BOARD": os.path.join(shared, "messages.jsonl"),
              "AGREE_LOG": os.path.join(shared, "agreement_log.jsonl"),
              "HARNESS_EVENTS": os.path.join(shared, "harness_events.jsonl")}
    subprocess.run([sys.executable, os.path.join(TOOLS, "agree.py"), "--log", common["AGREE_LOG"], "--agent", "setup",
                    "init", "--participants", "agent1,agent2,agent3"], check=True, capture_output=True)
    agents = {}
    for aid, (_, deliv, _) in TASKS.items():
        repo = os.path.join(tdir, aid, "repo")
        shutil.copytree(os.path.join(ROOT, TEMPLATE[aid]), repo)
        os.makedirs(os.path.join(repo, ".claude"))
        settings = {}
        if cond == "enforced":
            settings = {"hooks": {"PreToolUse": [{"matcher": "Write|Edit|MultiEdit|Bash", "hooks": [
                {"type": "command", "command": f"python3 {ROOT}/harness/gate.py"}]}]}}
        json.dump(settings, open(os.path.join(repo, ".claude", "settings.json"), "w"))
        agents[aid] = (repo, dict(common, AGENT_ID=aid, MY_FILE=os.path.join(repo, deliv)))
    return tdir, agents


def launch(aid, repo, env, cond, model, max_turns):
    who, _, task = TASKS[aid]
    rule = ("\n" + RULE.format(tools=TOOLS) + "\n") if cond == "advisory" else ""
    prompt = COMMON.format(who=who, repo=repo, tools=TOOLS, rule=rule, standard=STANDARDS[aid]) + "\n" + task
    full_env = {k: v for k, v in os.environ.items() if k not in ("CLAUDE_CODE_REMOTE_SDK_URL", "SESSION_INGRESS_URL")}
    full_env.update(env)
    tools = ["Read", "Write", "Edit", "Glob", "Grep", "Bash"]
    allowed = ["Read", "Write", "Edit", "Glob", "Grep", "Bash(cd:*)", "Bash(python3:*)", "Bash(python:*)",
               "Bash(head:*)", "Bash(cat:*)", "Bash(ls:*)", "Bash(wc:*)", "Bash(sleep:*)", "Bash(echo:*)",
               "Bash(AGENT_ID=*)", "Bash(export:*)"]
    cmd = ["claude", "-p", prompt, "--tools", *tools, "--strict-mcp-config", "--model", model,
           "--setting-sources", "project", "--permission-mode", "default", "--allowedTools", *allowed,
           "--disallowedTools", "WebFetch", "WebSearch", "Task", "mcp__claude-in-chrome",
           "--max-turns", str(max_turns), "--output-format", "stream-json", "--verbose",
           "--session-id", str(uuid.uuid4()), "--no-session-persistence", "--add-dir", os.path.dirname(env["MSG_BOARD"])]
    adir = os.path.dirname(repo)
    open(os.path.join(adir, "prompt.txt"), "w").write(prompt)
    return subprocess.Popen(cmd, cwd=repo, env=full_env, stdout=open(os.path.join(adir, "stream.jsonl"), "w"),
                            stderr=open(os.path.join(adir, "stderr.txt"), "w"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cond", choices=["baseline", "advisory", "enforced"])
    ap.add_argument("rep", type=int)
    ap.add_argument("--model", default="haiku")
    ap.add_argument("--max-turns", type=int, default=60)
    ap.add_argument("--timeout", type=int, default=1200)
    a = ap.parse_args()
    tdir, agents = setup(a.cond, a.rep)
    t0 = time.time()
    procs = {aid: launch(aid, repo, env, a.cond, a.model, a.max_turns) for aid, (repo, env) in agents.items()}
    for p in procs.values():
        try:
            p.wait(timeout=max(1, a.timeout - (time.time() - t0)))
        except subprocess.TimeoutExpired:
            p.kill()
    for aid in agents:
        last = None
        for line in open(os.path.join(tdir, aid, "stream.jsonl")):
            try:
                ev = json.loads(line)
            except json.JSONDecodeError:
                continue
            if ev.get("type") == "result":
                last = ev
        json.dump(last or {"is_error": True, "subtype": "no_result"}, open(os.path.join(tdir, aid, "result.json"), "w"))
    json.dump({"cond": a.cond, "rep": a.rep, "model": a.model, "wall_s": round(time.time() - t0, 1)},
              open(os.path.join(tdir, "trial.json"), "w"))
    print(f"done {a.cond} r{a.rep} in {time.time() - t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
