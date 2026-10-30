#!/usr/bin/env python3
"""Harness-side enforcement for the agent-agreement protocol (Claude Code hooks).

Two modes, both read the hook JSON from stdin and exit 2 to block:

  pre-tool   (PreToolUse on Edit|Write|MultiEdit)
             Block writing a file whose topic is not yet committed.
  stop       (Stop / SubagentStop / TaskCompleted)
             Block finishing while any of this agent's outputs fail Conf(o, d)
             and no deviation was announced.

Mapping from files to topics lives in $AGREE_SCOPE (JSON):
  {"agent1": {"src/encode.py": ["api.encode.signature"]}, "agent2": {...}}
Paths are matched with fnmatch globs.
"""
import fnmatch
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "agent-agreement", "scripts"))
import agree  # noqa: E402

LOG = os.environ.get("AGREE_LOG", "agreement_log.jsonl")
SCOPE = os.environ.get("AGREE_SCOPE", "agreement_scope.json")
AGENT = os.environ.get("AGENT_ID", "agent")


def scope_for(agent):
    if not os.path.exists(SCOPE):
        return {}
    with open(SCOPE) as f:
        return json.load(f).get(agent, {})


def topics_of(path, scope):
    rel = os.path.relpath(path) if os.path.isabs(path) else path
    out = []
    for pattern, topics in scope.items():
        if fnmatch.fnmatch(rel, pattern):
            out.extend(topics)
    return out


def block(msg):
    print(msg, file=sys.stderr)  # shown to the agent
    sys.exit(2)


def pre_tool(event):
    path = (event.get("tool_input") or {}).get("file_path")
    if not path:
        return
    _, topics = agree.state(agree._read(LOG))
    pending = [t for t in topics_of(path, scope_for(AGENT))
               if not (topics.get(t) or {}).get("committed")]
    if pending:
        block(f"[agreement] {path} depends on uncommitted topic(s): {', '.join(pending)}. "
              f"Agree first: scripts/agree.py status / propose / respond / commit.")


def stop(_event):
    _, topics = agree.state(agree._read(LOG))
    failures = []
    for pattern, ts in scope_for(AGENT).items():
        if any(ch in pattern for ch in "*?["):
            continue  # stop-time checks need concrete output paths
        for t in ts:
            dev = [d for d in (topics.get(t) or {}).get("deviations", []) if d["agent"] == AGENT]
            if dev:
                continue
            ok, msg = agree.run_check(LOG, t, pattern)
            if not ok:
                failures.append(f"{t} on {pattern}: {msg}")
    if failures:
        block("[agreement] outputs do not conform to committed decisions:\n- "
              + "\n- ".join(failures)
              + "\nFix them, or run scripts/agree.py deviate TOPIC --why ...")


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "pre-tool"
    try:
        event = json.load(sys.stdin)
    except json.JSONDecodeError:
        event = {}
    {"pre-tool": pre_tool, "stop": stop}[mode](event)
    sys.exit(0)
