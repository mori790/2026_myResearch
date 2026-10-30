#!/usr/bin/env python3
"""Harness for experiment 1 (Claude Code hooks). Exit 2 blocks.

pre-tool : block writing the deliverable (Write/Edit to out/*, or Bash touching out/)
           while topic data.outlier_rule is not committed in the shared log.
stop     : block finishing if the deliverable does not conform to the committed rule.
"""
import json, os, subprocess, sys

TOOLS = os.environ["TOOLS"]
sys.path.insert(0, TOOLS)
import agree  # noqa: E402

LOG = os.environ["AGREE_LOG"]
TOPIC = "data.outlier_rule"
OUT = os.environ["OUT_FILE"]          # absolute path of this agent's deliverable
HOW = (f"Use the agreement tool first: python3 $TOOLS/agree.py status | "
       f"propose {TOPIC} '{{\"method\": ..., \"k\": ...}}' | respond {TOPIC} accept|object | commit {TOPIC}. "
       f"Your teammate must accept before you can commit.")


def committed():
    _, topics = agree.state(agree._read(LOG))
    t = topics.get(TOPIC) or {}
    return t.get("committed")


def touches_out(event):
    ti = event.get("tool_input") or {}
    if event.get("tool_name") in ("Write", "Edit", "MultiEdit", "NotebookEdit"):
        return os.path.abspath(ti.get("file_path", "")).startswith(os.path.dirname(OUT))
    if event.get("tool_name") == "Bash":
        return os.path.dirname(OUT) in ti.get("command", "") or " out/" in ti.get("command", "") \
            or "'out/" in ti.get("command", "") or '"out/' in ti.get("command", "")
    return False


def block(msg):
    print(msg, file=sys.stderr)
    with open(os.environ["HARNESS_EVENTS"], "a") as f:
        f.write(json.dumps({"agent": os.environ["AGENT_ID"], "block": msg[:200]}) + "\n")
    sys.exit(2)


def pre_tool(event):
    if touches_out(event) and not committed():
        block(f"[harness] Writing your report is blocked: topic '{TOPIC}' is not committed yet. {HOW}")


def stop(event):
    if event.get("stop_hook_active"):
        return  # avoid infinite loops: block at most once per stop
    c = committed()
    if not c:
        block(f"[harness] You cannot finish: topic '{TOPIC}' is not committed. {HOW}")
    r = subprocess.run([sys.executable, os.path.join(TOOLS, "check_output.py"), OUT, json.dumps(c["value"])],
                       capture_output=True, text=True)
    if r.returncode != 0:
        block(f"[harness] Your report does not conform to the committed rule {c['value']}: {r.stdout.strip()} Fix it.")


if __name__ == "__main__":
    ev = json.load(sys.stdin) if not sys.stdin.isatty() else {}
    {"pre-tool": pre_tool, "stop": stop}[sys.argv[1]](ev)
