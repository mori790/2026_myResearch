#!/usr/bin/env python3
"""Experiment 2: two coding agents (pricing.py / invoice.py) in separate workspaces.

usage: run_trial.py CONDITION REP [--model haiku]
CONDITION: base | skill | ci | skill_ci
  base     : message board only
  skill    : + agent-agreement skill (and the prompt says it exists)
  ci       : + harness CI gate on Stop (merges both modules, runs the public example)
  skill_ci : both
"""
import argparse, json, os, shutil, subprocess, sys, time, uuid

ROOT = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.join(ROOT, "tools")

COMMON = """You are {who} on a two-person team building a small Python invoicing package. Your teammate is {other};
they work in parallel with you right now in their own copy of the repository, and you cannot see each other's files.

Repository (your copy): {repo}
- pricing.py : owned by agent1 (pricing developer)
- invoice.py : owned by agent2 (invoice developer); it must get every price, discount and customer name by calling pricing.py
- data/catalog.csv (sku,name,price in dollars like 12.50), data/customers.csv (id,name,discount like 10%)

At the end, agent1's pricing.py and agent2's invoice.py will be put together and tested.

To talk to your teammate:
  python3 {tools}/msg.py send "your message"
  python3 {tools}/msg.py read
  python3 {tools}/msg.py wait 60     (waits up to 60 s for a new message)
{skill_line}
"""

TASK1 = """YOUR TASK: implement the three functions in pricing.py exactly as their docstrings describe
(price_of, discount_for, customer_name). Only pricing.py counts as your deliverable.
When pricing.py is done, stop."""

TASK2 = """YOUR TASK: implement render_invoice(order) in invoice.py. Only invoice.py counts as your deliverable
(the pricing.py in your copy is just a stub; agent1 writes the real one).

Exact output format (lines joined with "\\n", no trailing newline). For the order
{{"customer": "C1", "lines": [["A", 2], ["Z", 1]]}} the output must be:
Customer: Alice
A x2 @ $12.50 = $25.00
UNKNOWN SKU: Z
Subtotal: $25.00
Discount (10%): -$2.50
Total: $22.50

Rules: line amount = price * qty; amounts rounded to the nearest cent (half up); unknown skus are listed as
"UNKNOWN SKU: <sku>" and skipped; the discount line always appears (shown as a whole percent, e.g. 0%);
an unknown customer is shown by its id with 0% discount.
When invoice.py is done, stop."""

TOOL_LINE = ("A command-line tool for recording decisions you and your teammate agree on is available: "
             "python3 {tools}/agree.py --help")

SKILL_LINE = ("A skill named `agent-agreement` is available to you for agreeing on shared decisions with your teammate "
              "(scripts: python3 {tools}/agree.py ...).")


def setup(cond, rep):
    tdir = os.path.join(ROOT, "runs", f"{cond}_r{rep}")
    if os.path.exists(tdir):
        shutil.rmtree(tdir)
    shared = os.path.join(tdir, "shared")
    os.makedirs(shared)
    common = {"TOOLS": TOOLS, "EVAL_DIR": os.path.join(ROOT, "eval"),
              "MSG_BOARD": os.path.join(shared, "messages.jsonl"),
              "AGREE_LOG": os.path.join(shared, "agreement_log.jsonl"),
              "HARNESS_EVENTS": os.path.join(shared, "harness_events.jsonl"),
              "PRICING_FILE": os.path.join(tdir, "agent1", "repo", "pricing.py"),
              "INVOICE_FILE": os.path.join(tdir, "agent2", "repo", "invoice.py")}
    if cond in ("skill", "skill_ci", "tool", "inline", "gate"):
        subprocess.run([sys.executable, os.path.join(TOOLS, "agree.py"), "--log", common["AGREE_LOG"],
                        "--agent", "setup", "init", "--participants", "agent1,agent2"], check=True, capture_output=True)
    agents = {}
    for aid in ("agent1", "agent2"):
        adir = os.path.join(tdir, aid)
        repo = os.path.join(adir, "repo")
        shutil.copytree(os.path.join(ROOT, "repo_template"), repo)
        os.makedirs(os.path.join(repo, ".claude"))
        settings = {}
        if cond in ("ci", "skill_ci"):
            settings = {"hooks": {"Stop": [{"hooks": [{"type": "command",
                        "command": f"python3 {ROOT}/harness/ci_gate.py"}]}]}}
        elif cond == "ci_barrier":
            settings = {"hooks": {"Stop": [{"hooks": [{"type": "command",
                        "command": f"python3 {ROOT}/harness/ci_barrier.py"}]}]}}
        elif cond == "gate":
            settings = {"hooks": {"PreToolUse": [{"matcher": "Write|Edit|MultiEdit|Bash", "hooks": [{"type": "command",
                        "command": f"python3 {ROOT}/harness/gate_before.py"}]}]}}
        json.dump(settings, open(os.path.join(repo, ".claude", "settings.json"), "w"))
        if "skill" in cond:
            sdir = os.path.join(repo, ".claude", "skills", "agent-agreement")
            os.makedirs(sdir)
            shutil.copy(os.path.join(ROOT, "skill", "SKILL.md"), sdir)
        my_file = os.path.join(repo, "pricing.py" if aid == "agent1" else "invoice.py")
        agents[aid] = (repo, dict(common, AGENT_ID=aid, MY_FILE=my_file))
    return tdir, agents


def launch(aid, repo, env, cond, model, max_turns):
    who, other, task = (("agent1, the PRICING developer", "agent2", TASK1) if aid == "agent1"
                        else ("agent2, the INVOICE developer", "agent1", TASK2))
    if cond in ("skill", "skill_ci"):
        skill_line = SKILL_LINE.format(tools=TOOLS)
    elif cond == "tool":
        skill_line = TOOL_LINE.format(tools=TOOLS)
    elif cond == "inline":
        body = open(os.path.join(ROOT, "skill", "SKILL.md")).read().split("---", 2)[2]
        skill_line = ("Follow this procedure for agreeing on shared decisions with your teammate:\n"
                      + body.replace("$TOOLS", TOOLS))
    else:
        skill_line = ""
    prompt = COMMON.format(who=who, other=other, repo=repo, tools=TOOLS, skill_line=skill_line) + "\n" + task
    full_env = {k: v for k, v in os.environ.items() if k not in ("CLAUDE_CODE_REMOTE_SDK_URL", "SESSION_INGRESS_URL")}
    full_env.update(env)
    tools = ["Read", "Write", "Edit", "Glob", "Grep", "Bash", "Skill"]
    allowed = ["Read", "Write", "Edit", "Glob", "Grep", "Skill", "Bash(cd:*)", "Bash(python3:*)",
               "Bash(head:*)", "Bash(cat:*)", "Bash(ls:*)", "Bash(wc:*)", "Bash(sleep:*)"]
    cmd = ["claude", "-p", prompt, "--tools", *tools, "--strict-mcp-config", "--model", model,
           "--setting-sources", "project", "--permission-mode", "default", "--allowedTools", *allowed,
           "--disallowedTools", "WebFetch", "WebSearch", "Task", "mcp__claude-in-chrome",
           "--max-turns", str(max_turns), "--output-format", "stream-json", "--verbose",
           "--session-id", str(uuid.uuid4()), "--no-session-persistence", "--add-dir", os.path.dirname(env["MSG_BOARD"])]
    adir = os.path.dirname(repo)
    return subprocess.Popen(cmd, cwd=repo, env=full_env, stdout=open(os.path.join(adir, "stream.jsonl"), "w"),
                            stderr=open(os.path.join(adir, "stderr.txt"), "w"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cond", choices=["base", "tool", "inline", "skill", "gate", "ci", "ci_barrier", "skill_ci"])
    ap.add_argument("rep", type=int)
    ap.add_argument("--model", default="haiku")
    ap.add_argument("--max-turns", type=int, default=40)
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
    print(f"done {a.cond} r{a.rep} in {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
