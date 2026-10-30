#!/usr/bin/env python3
"""Harness 'gate' (PreToolUse): you may not write your deliverable until the team has
committed an interface decision (topic 'interface') in the shared agreement log. Exit 2 blocks."""
import json, os, sys

sys.path.insert(0, os.environ["TOOLS"])
import agree  # noqa: E402

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
    _, topics = agree.state(agree._read(os.environ["AGREE_LOG"]))
    if (topics.get("interface") or {}).get("committed"):
        return
    msg = ("[harness] You cannot write " + os.path.basename(DELIV) + " yet: your team has not committed the interface "
           "between pricing.py and invoice.py. Agree on it first and record it:\n"
           f"  python3 {TOOLS}/agree.py propose interface '<the exact interface you agree on>'\n"
           f"  (your teammate runs) python3 {TOOLS}/agree.py respond interface accept\n"
           f"  python3 {TOOLS}/agree.py commit interface\n"
           f"Check status with python3 {TOOLS}/agree.py status")
    with open(os.environ["HARNESS_EVENTS"], "a") as f:
        f.write(json.dumps({"agent": os.environ["AGENT_ID"], "block": "gate"}) + "\n")
    print(msg, file=sys.stderr)
    sys.exit(2)


if __name__ == "__main__":
    main()
