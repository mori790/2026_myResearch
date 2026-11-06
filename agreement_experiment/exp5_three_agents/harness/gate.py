#!/usr/bin/env python3
"""Enforced condition (PreToolUse hook): block writes to the agent's own deliverable until the
team rule holds (>=1 committed decision, no open proposal). Exit code 2 blocks the tool call."""
import json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
sys.path.insert(0, ROOT)
import agree  # noqa: E402
from rule import RULE, ready  # noqa: E402

DELIV = os.environ["MY_FILE"]
TOOLS = os.environ["TOOLS"]


def touches(ev):
    ti = ev.get("tool_input") or {}
    if ev.get("tool_name") in ("Write", "Edit", "MultiEdit"):
        return os.path.abspath(ti.get("file_path", "")) == DELIV
    if ev.get("tool_name") == "Bash":
        cmd = ti.get("command", "")
        if "agree.py" in cmd or "msg.py" in cmd:
            return False  # never block the coordination tools themselves
        return os.path.basename(DELIV) in cmd and any(t in cmd for t in (">", "write", "open(", "sed -i", "tee", "cp ", "mv "))
    return False


def main():
    ev = json.load(sys.stdin)
    if not touches(ev):
        return
    ok, committed, open_ = ready(agree.state(agree._read(os.environ["AGREE_LOG"]))[1])
    if ok:
        return
    why = "no decision is committed yet" if not committed else "these proposals are still open: " + ", ".join(open_)
    with open(os.environ["HARNESS_EVENTS"], "a") as f:
        f.write(json.dumps({"agent": os.environ["AGENT_ID"], "block": "gate", "why": why}) + "\n")
    print(f"[harness] Blocked: you cannot write {os.path.basename(DELIV)} yet ({why}).\n\n" + RULE.format(tools=TOOLS),
          file=sys.stderr)
    sys.exit(2)


if __name__ == "__main__":
    main()
