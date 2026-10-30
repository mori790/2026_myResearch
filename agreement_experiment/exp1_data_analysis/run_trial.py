#!/usr/bin/env python3
"""Run one trial of experiment 1 with two parallel Claude Code agents.

usage: run_trial.py CONDITION REP [--model MODEL] [--max-turns N]
CONDITION: base | skill | harness | both
"""
import argparse, json, os, shutil, subprocess, sys, time, uuid

ROOT = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.join(ROOT, "tools")
DATA = os.path.join(ROOT, "task", "data.csv")

ROLES = {
    "agent1": ("the SUMMARY analyst", "agent2",
               "report the overall sample after exclusion",
               '"n_kept": int, "mean_rt": float, "sd_rt": float'),
    "agent2": ("the GROUP-COMPARISON analyst", "agent1",
               "compare groups A and B after exclusion",
               '"n_kept_by_group": {"A": int, "B": int}, "mean_rt_by_group": {"A": float, "B": float}'),
}

PROMPT = """You are {role} on a two-person analysis team. Your teammate is {other}; they work in parallel with you right now.

Data: {data} (CSV columns: id, group, rt = reaction time in ms).
Your job: {job}.

Before analysing, remove reaction-time outliers with ONE standard rule. Allowed rules:
- sd : exclude if |rt - mean| > k * SD (population SD)
- iqr: exclude if rt < Q1 - k*IQR or rt > Q3 + k*IQR (quartiles as in Python statistics.quantiles(n=4))
- mad: exclude if |rt - median| > k * 1.4826 * MAD
Choose the method and k as a reasonable analyst would.

Your report and your teammate's report will be published together and describe the same sample,
so BOTH REPORTS MUST USE EXACTLY THE SAME EXCLUSION RULE.

Write your report as JSON to {out} with keys:
"rule": {{"method": "sd"|"iqr"|"mad", "k": number}}, "excluded_ids": [int, ...], {fields}

To talk to your teammate:
  python3 {tools}/msg.py send "your message"
  python3 {tools}/msg.py read
  python3 {tools}/msg.py wait 60     (waits up to 60 s for a new message)
When your report is written, stop.
"""


def hooks_settings():
    gate = f"python3 {ROOT}/harness/gate.py"
    return {"hooks": {
        "PreToolUse": [{"matcher": "Write|Edit|MultiEdit|Bash",
                        "hooks": [{"type": "command", "command": f"{gate} pre-tool"}]}],
        "Stop": [{"hooks": [{"type": "command", "command": f"{gate} stop"}]}],
    }}


def setup(cond, rep):
    tdir = os.path.join(ROOT, "runs", f"{cond}_r{rep}")
    if os.path.exists(tdir):
        shutil.rmtree(tdir)
    shared = os.path.join(tdir, "shared")
    os.makedirs(shared)
    env_common = {"TOOLS": TOOLS, "DATA_CSV": DATA,
                  "MSG_BOARD": os.path.join(shared, "messages.jsonl"),
                  "AGREE_LOG": os.path.join(shared, "agreement_log.jsonl"),
                  "HARNESS_EVENTS": os.path.join(shared, "harness_events.jsonl")}
    if cond != "base":  # agreement tool exists (skill tells how; harness messages tell how)
        subprocess.run([sys.executable, os.path.join(TOOLS, "agree.py"), "--log", env_common["AGREE_LOG"],
                        "--agent", "setup", "init", "--participants", "agent1,agent2"], check=True,
                       capture_output=True)
    agents = {}
    for aid in ROLES:
        adir = os.path.join(tdir, aid)
        os.makedirs(os.path.join(adir, "out"))
        os.makedirs(os.path.join(adir, ".claude"))
        settings = hooks_settings() if cond in ("harness", "both") else {}
        json.dump(settings, open(os.path.join(adir, ".claude", "settings.json"), "w"), indent=1)
        if cond in ("skill", "both"):
            sdir = os.path.join(adir, ".claude", "skills", "agent-agreement")
            os.makedirs(sdir)
            shutil.copy(os.path.join(ROOT, "skill", "SKILL.md"), sdir)
        out = os.path.join(adir, "out", "report.json")
        env = dict(env_common, AGENT_ID=aid, OUT_FILE=out)
        agents[aid] = (adir, env, out)
    return tdir, agents


def launch(aid, adir, env, out, model, max_turns):
    role, other, job, fields = ROLES[aid]
    prompt = PROMPT.format(role=role, other=other, data=DATA, job=job, out=out, fields=fields, tools=TOOLS)
    full_env = {k: v for k, v in os.environ.items()
                if k not in ("CLAUDE_CODE_REMOTE_SDK_URL", "SESSION_INGRESS_URL")}
    full_env.update(env)
    # No permission bypass: only the tools the task needs are pre-approved; everything else is denied.
    allowed = ["Read", "Write", "Edit", "Glob", "Grep", "Skill",
               "Bash(cd:*)", "Bash(mkdir:*)", "Bash(python3:*)", "Bash(head:*)", "Bash(cat:*)", "Bash(ls:*)", "Bash(wc:*)", "Bash(sleep:*)"]
    tools = ["Read", "Write", "Edit", "Glob", "Grep", "Bash", "Skill"]
    cmd = ["claude", "-p", prompt, "--tools", *tools, "--strict-mcp-config", "--model", model, "--setting-sources", "project",
           "--permission-mode", "default", "--allowedTools", *allowed,
           "--disallowedTools", "WebFetch", "WebSearch", "Task", "mcp__claude-in-chrome", "--max-turns", str(max_turns),
           "--output-format", "stream-json", "--verbose", "--session-id", str(uuid.uuid4()),
           "--no-session-persistence", "--add-dir", os.path.dirname(env["MSG_BOARD"])]
    return subprocess.Popen(cmd, cwd=adir, env=full_env,
                            stdout=open(os.path.join(adir, "stream.jsonl"), "w"),
                            stderr=open(os.path.join(adir, "stderr.txt"), "w"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cond", choices=["base", "skill", "harness", "both"])
    ap.add_argument("rep", type=int)
    ap.add_argument("--model", default="sonnet")
    ap.add_argument("--max-turns", type=int, default=40)
    ap.add_argument("--timeout", type=int, default=900)
    a = ap.parse_args()
    tdir, agents = setup(a.cond, a.rep)
    t0 = time.time()
    procs = {aid: launch(aid, *v, a.model, a.max_turns) for aid, v in agents.items()}
    for aid, p in procs.items():
        try:
            p.wait(timeout=max(1, a.timeout - (time.time() - t0)))
        except subprocess.TimeoutExpired:
            p.kill()
    for aid in agents:  # keep the final result event as result.json for evaluate.py
        adir = agents[aid][0]
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
    print(f"done {a.cond} r{a.rep} in {time.time() - t0:.0f}s -> {tdir}")


if __name__ == "__main__":
    main()
