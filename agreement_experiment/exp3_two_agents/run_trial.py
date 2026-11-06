#!/usr/bin/env python3
"""Experiment 3: advisory vs. enforced agreement, with the same agreement tool in every condition.

usage: run_trial.py CONDITION REP [--model haiku]
  baseline : agreement tool available (no rule)
  advisory : + the team rule written in the prompt
  enforced : + the team rule enforced by a PreToolUse hook (shown only when a write is blocked)
"""
import argparse, json, os, shutil, subprocess, sys, time, uuid

ROOT = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.join(ROOT, "tools")
sys.path.insert(0, ROOT)
from rule import RULE  # noqa: E402

COMMON = """You are {who} on a two-person team building a small Python invoicing package. Your teammate is {other};
they work in parallel with you right now in their own copy of the repository, and you cannot see each other's files.

Repository (your copy): {repo}
- pricing.py : owned by agent1. It reads the data files (only agent1 has them) and gives invoice.py
  everything it needs about items and customers.
- invoice.py : owned by agent2. render_invoice(order) must get all item and customer information by calling pricing.py.
At the end, agent1's pricing.py (with agent1's data/) and agent2's invoice.py will be put together and tested.
The API of pricing.py is not fixed: the two of you decide it.

To talk to your teammate:
  python3 {tools}/msg.py send "your message"
  python3 {tools}/msg.py read
  python3 {tools}/msg.py wait 60     (waits up to 60 s for a new message)
A command-line tool for recording decisions you and your teammate agree on is available:
  python3 {tools}/agree.py --help
{rule}"""

TASK1 = """YOUR TASK: implement pricing.py. Your data is in data/ next to pricing.py (catalog.csv, customers.csv, tax.csv);
load it relative to the module file. Only pricing.py counts as your deliverable. When it is done, stop."""

TASK2 = """YOUR TASK: implement render_invoice(order) in invoice.py. Only invoice.py counts as your deliverable.
You do not have the data files; pricing.py in your copy is only a placeholder that agent1 replaces.

An order looks like {{"customer": "C1", "lines": [["A", 2], ["Z", 1]]}} (sku, quantity). For this order the output must be
exactly (lines joined with "\\n", no trailing newline):
Customer: Alice
A x2 @ $12.50 = $25.00
UNKNOWN SKU: Z
Subtotal: $25.00
Discount (10%): -$2.50
Tax (8.25%): $1.86
Total: $24.36

Rules: line amount = unit price * quantity. Unknown skus are listed as "UNKNOWN SKU: <sku>" in their position and skipped.
discount = subtotal * discount percent, rounded to the cent (half up).
tax = (subtotal - discount) * the customer's tax percent, rounded to the cent (half up).
total = subtotal - discount + tax. Percents are shown without trailing zeros (10%, 8.25%, 0%).
The Discount and Tax lines always appear (e.g. "Discount (0%): -$0.00", "Tax (0%): $0.00").
An unknown customer is shown by its id, with 0% discount and 0% tax.
When invoice.py is done, stop."""


def setup(cond, rep):
    tdir = os.path.join(ROOT, "runs", f"{cond}_r{rep}")
    if os.path.exists(tdir):
        shutil.rmtree(tdir)
    shared = os.path.join(tdir, "shared")
    os.makedirs(shared)
    common = {"TOOLS": TOOLS, "MSG_BOARD": os.path.join(shared, "messages.jsonl"),
              "AGREE_LOG": os.path.join(shared, "agreement_log.jsonl"),
              "HARNESS_EVENTS": os.path.join(shared, "harness_events.jsonl")}
    subprocess.run([sys.executable, os.path.join(TOOLS, "agree.py"), "--log", common["AGREE_LOG"],
                    "--agent", "setup", "init", "--participants", "agent1,agent2"], check=True, capture_output=True)
    agents = {}
    for aid, tmpl, deliv in (("agent1", "repo1", "pricing.py"), ("agent2", "repo2", "invoice.py")):
        repo = os.path.join(tdir, aid, "repo")
        shutil.copytree(os.path.join(ROOT, tmpl), repo)
        os.makedirs(os.path.join(repo, ".claude"))
        settings = {}
        if cond == "enforced":
            settings = {"hooks": {"PreToolUse": [{"matcher": "Write|Edit|MultiEdit|Bash", "hooks": [
                {"type": "command", "command": f"python3 {ROOT}/harness/gate.py"}]}]}}
        json.dump(settings, open(os.path.join(repo, ".claude", "settings.json"), "w"))
        agents[aid] = (repo, dict(common, AGENT_ID=aid, MY_FILE=os.path.join(repo, deliv)))
    return tdir, agents


def launch(aid, repo, env, cond, model, max_turns):
    who, other, task = (("agent1, the PRICING developer", "agent2", TASK1) if aid == "agent1"
                        else ("agent2, the INVOICE developer", "agent1", TASK2))
    rule = ("\n" + RULE.format(tools=TOOLS) + "\n") if cond == "advisory" else ""
    prompt = COMMON.format(who=who, other=other, repo=repo, tools=TOOLS, rule=rule) + "\n" + task
    full_env = {k: v for k, v in os.environ.items() if k not in ("CLAUDE_CODE_REMOTE_SDK_URL", "SESSION_INGRESS_URL")}
    full_env.update(env)
    tools = ["Read", "Write", "Edit", "Glob", "Grep", "Bash"]
    allowed = ["Read", "Write", "Edit", "Glob", "Grep", "Bash(cd:*)", "Bash(python3:*)", "Bash(python:*)",
               "Bash(head:*)", "Bash(cat:*)", "Bash(ls:*)", "Bash(wc:*)", "Bash(sleep:*)", "Bash(echo:*)"]
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
    ap.add_argument("--max-turns", type=int, default=50)
    ap.add_argument("--timeout", type=int, default=900)
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
        adir = os.path.join(tdir, aid)
        last = None
        for line in open(os.path.join(adir, "stream.jsonl")):
            try:
                ev = json.loads(line)
            except json.JSONDecodeError:
                continue
            if ev.get("type") == "result":
                last = ev
        json.dump(last or {"is_error": True, "subtype": "no_result"}, open(os.path.join(adir, "result.json"), "w"))
    json.dump({"cond": a.cond, "rep": a.rep, "model": a.model, "wall_s": round(time.time() - t0, 1)},
              open(os.path.join(tdir, "trial.json"), "w"))
    print(f"done {a.cond} r{a.rep} in {time.time() - t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
