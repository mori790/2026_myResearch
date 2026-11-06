#!/usr/bin/env python3
"""Enforced condition (PreToolUse hook on Bash): a remediation command (ops.py restart/set-config/scale/failover)
is blocked unless the caller is the commander in the latest committed decision. Exit code 2 blocks."""
import json, os, re, shlex, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools")); sys.path.insert(0, ROOT)
import agree  # noqa: E402
from rule import RULE, commander  # noqa: E402

VERBS = {"restart", "set-config", "scale", "failover"}


def is_remediation(cmd):
    """True if the command actually invokes ops.py with a remediation verb (not merely mentions it in a message)."""
    try:
        lex = shlex.shlex(cmd, posix=True, punctuation_chars=";&|")
        lex.whitespace_split = True
        toks = list(lex)
    except ValueError:
        return bool(re.search(r"ops\.py\s+(restart|set-config|scale|failover)\b", cmd))
    return any(t.endswith("ops.py") and i + 1 < len(toks) and toks[i + 1] in VERBS for i, t in enumerate(toks))


def main():
    ev = json.load(sys.stdin)
    if ev.get("tool_name") != "Bash":
        return
    cmd = (ev.get("tool_input") or {}).get("command", "")
    if not is_remediation(cmd):
        return
    me = os.environ["AGENT_ID"]
    c = commander(agree.state(agree._read(os.environ["AGREE_LOG"]))[1])
    if c == me:
        return
    why = "no commander is committed yet" if c is None else f"the committed commander is {c}, not you"
    with open(os.environ["HARNESS_EVENTS"], "a") as f:
        f.write(json.dumps({"agent": me, "block": "remediation", "why": why, "cmd": cmd[:200]}) + "\n")
    print(f"[harness] Blocked: {why}.\n\n" + RULE.format(tools=os.environ["TOOLS"]), file=sys.stderr)
    sys.exit(2)


if __name__ == "__main__":
    main()
