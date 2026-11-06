#!/usr/bin/env python3
"""Agreement primitive: append-only decision log shared by several agents.

Operations (all take --log PATH, default $AGREE_LOG or ./agreement_log.jsonl):
  init      --participants a1,a2,...         declare who must agree
  propose   TOPIC VALUE_JSON [--why TEXT]     open a new version of TOPIC
  respond   TOPIC accept|object [--why TEXT]  vote on the open version
  commit    TOPIC                             finalize if everyone accepted
  lookup    TOPIC                             print latest committed decision
  status    [TOPIC]                           show open/committed topics
  checker   TOPIC COMMAND                     register a conformance checker
  check     TOPIC OUTPUT_PATH                 run Conf(output, decision)
  deviate   TOPIC --why TEXT                  announce you cannot conform
  withdraw  TOPIC [--why TEXT]                abort the open proposal on TOPIC (any participant)
  leave                                       you are finished: later votes no longer wait for you

The calling agent is identified by $AGENT_ID (or --agent).
Each log entry is hash-chained to the previous one, so edits are detectable.
"""
import argparse
import fcntl
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import time

EXIT_OK, EXIT_FAIL, EXIT_USAGE = 0, 1, 2


# ---------------------------------------------------------------- log I/O
def _read(path):
    if not os.path.exists(path):
        return []
    with open(path) as f:
        return [json.loads(line) for line in f if line.strip()]


def _append(path, entry, guard=None):
    """Append one entry under an exclusive lock, chaining its hash.

    `guard(entries)` runs while the lock is held, so checks and the write are atomic.
    It may return a replacement entry, or call sys.exit to refuse the write."""
    with open(path, "a+") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        try:
            f.seek(0)
            lines = [l for l in f.read().splitlines() if l.strip()]
            if guard is not None:
                entry = guard([json.loads(l) for l in lines]) or entry
            prev = json.loads(lines[-1])["hash"] if lines else "genesis"
            entry = dict(entry, seq=len(lines), ts=time.time(), prev=prev)
            body = json.dumps(entry, sort_keys=True, ensure_ascii=False)
            entry["hash"] = hashlib.sha256(body.encode()).hexdigest()[:16]
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
            f.flush()
        finally:
            fcntl.flock(f, fcntl.LOCK_UN)
    return entry


def verify_chain(entries):
    prev = "genesis"
    for e in entries:
        body = {k: v for k, v in e.items() if k != "hash"}
        h = hashlib.sha256(json.dumps(body, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:16]
        if e["prev"] != prev or e["hash"] != h:
            return False
        prev = e["hash"]
    return True


# ---------------------------------------------------------------- state
def state(entries):
    """Replay the log into per-topic state."""
    participants, topics = [], {}
    for e in entries:
        k = e["kind"]
        if k == "init":
            participants = list(e["participants"])
            continue
        if k == "leave":
            participants = [p for p in participants if p != e["agent"]]
            continue
        t = topics.setdefault(e.get("topic"), {
            "version": 0, "open": None, "committed": None,
            "checker": None, "deviations": [], "history": []})
        if k == "propose":
            t["version"] += 1
            t["open"] = {"version": t["version"], "value": e["value"],
                         "by": e["agent"], "votes": {e["agent"]: "accept"}}
        elif k == "respond" and t["open"] and e["version"] == t["open"]["version"]:
            t["open"]["votes"][e["agent"]] = e["vote"]
        elif k == "commit":
            t["committed"] = {"version": e["version"], "value": e["value"]}
            t["history"].append(t["committed"])
            t["open"] = None
        elif k == "abort":
            t["open"] = None
        elif k == "checker":
            t["checker"] = e["command"]
        elif k == "deviate":
            t["deviations"].append({"agent": e["agent"], "why": e["why"],
                                    "version": e.get("version")})
    return participants, topics


def committed_value(log, topic):
    _, topics = state(_read(log))
    t = topics.get(topic)
    return t["committed"] if t else None


# ---------------------------------------------------------------- commands
def cmd_init(a):
    _append(a.log, {"kind": "init", "agent": a.agent,
                    "participants": [p.strip() for p in a.participants.split(",")]})
    print("initialized")


def cmd_propose(a):
    try:
        value = json.loads(a.value)
    except json.JSONDecodeError:
        value = a.value

    def guard(entries):
        participants, topics = state(entries)
        if a.agent not in participants:
            sys.exit(f"error: {a.agent} is not a participant")
        t = topics.get(a.topic)
        if t and t["open"]:
            sys.exit(f"error: {a.topic} v{t['open']['version']} is still open; respond to it first")
    _append(a.log, {"kind": "propose", "agent": a.agent, "topic": a.topic, "value": value, "why": a.why}, guard)
    _, topics = state(_read(a.log))
    print(f"proposed {a.topic} v{topics[a.topic]['version']}: {json.dumps(value, ensure_ascii=False)}")
    others = [n for n in topics if n and n != a.topic]
    if others:
        print("other topics in the log: " + ", ".join(others))


def cmd_respond(a):
    seen = {}

    def guard(entries):
        _, topics = state(entries)
        t = topics.get(a.topic)
        if not t or not t["open"]:
            sys.exit(f"error: no open proposal for {a.topic}")
        seen["v"] = t["open"]["version"]
        return {"kind": "respond", "agent": a.agent, "topic": a.topic,
                "version": seen["v"], "vote": a.vote, "why": a.why}
    _append(a.log, {}, guard)
    print(f"{a.agent} -> {a.vote} on {a.topic} v{seen['v']}")


def cmd_commit(a):
    out = {}

    def guard(entries):
        participants, topics = state(entries)
        t = topics.get(a.topic)
        if not t or not t["open"]:
            sys.exit(f"error: no open proposal for {a.topic}")
        votes, v = t["open"]["votes"], t["open"]["version"]
        if any(x == "object" for x in votes.values()):
            out["msg"] = (f"aborted {a.topic} v{v}: objection from "
                          + ", ".join(p for p, x in votes.items() if x == "object"))
            out["fail"] = True
            return {"kind": "abort", "agent": a.agent, "topic": a.topic, "version": v}
        missing = [p for p in participants if votes.get(p) != "accept"]
        if missing:
            sys.exit(f"waiting on {a.topic} v{v}: no response yet from {', '.join(missing)}")
        out["msg"] = f"committed {a.topic} v{v}: {json.dumps(t['open']['value'], ensure_ascii=False)}"
        return {"kind": "commit", "agent": a.agent, "topic": a.topic, "version": v, "value": t["open"]["value"]}
    _append(a.log, {}, guard)
    print(out["msg"])
    if out.get("fail"):
        sys.exit(EXIT_FAIL)


def cmd_lookup(a):
    c = committed_value(a.log, a.topic)
    if not c:
        print(f"{a.topic}: not committed")
        sys.exit(EXIT_FAIL)
    print(json.dumps({"topic": a.topic, **c}, ensure_ascii=False))


def cmd_status(a):
    entries = _read(a.log)
    participants, topics = state(entries)
    print(f"participants: {', '.join(participants) or '(none)'}")
    print(f"log integrity: {'ok' if verify_chain(entries) else 'BROKEN'}")
    for name, t in topics.items():
        if a.topic and name != a.topic:
            continue
        c = t["committed"]
        line = f"- {name}: " + (f"committed v{c['version']} = {json.dumps(c['value'], ensure_ascii=False)}" if c else "not committed")
        if t["open"]:
            line += f" | open v{t['open']['version']} votes={t['open']['votes']}"
        if t["deviations"]:
            line += f" | deviations={len(t['deviations'])}"
        print(line)


def cmd_checker(a):
    _append(a.log, {"kind": "checker", "agent": a.agent, "topic": a.topic, "command": a.command})
    print(f"checker registered for {a.topic}")


def run_check(log, topic, output):
    """Return (ok, message). Checker gets the decision via $DECISION_FILE."""
    _, topics = state(_read(log))
    t = topics.get(topic)
    if not t or not t["committed"]:
        return False, f"{topic}: no committed decision"
    if not t["checker"]:
        return False, f"{topic}: no checker registered"
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        json.dump(t["committed"]["value"], f, ensure_ascii=False)
        dfile = f.name
    env = dict(os.environ, DECISION_FILE=dfile, OUTPUT_PATH=output)
    r = subprocess.run(t["checker"], shell=True, env=env, capture_output=True, text=True)
    os.unlink(dfile)
    msg = (r.stdout + r.stderr).strip()
    return r.returncode == 0, msg


def cmd_check(a):
    ok, msg = run_check(a.log, a.topic, a.output)
    print(("PASS " if ok else "FAIL ") + f"{a.topic}: {msg}")
    sys.exit(EXIT_OK if ok else EXIT_FAIL)


def cmd_withdraw(a):
    def guard(entries):
        _, topics = state(entries)
        t = topics.get(a.topic)
        if not t or not t["open"]:
            sys.exit(f"error: no open proposal for {a.topic}")
        return {"kind": "abort", "agent": a.agent, "topic": a.topic, "version": t["open"]["version"],
                "why": a.why or "withdrawn"}
    e = _append(a.log, {}, guard)
    print(f"withdrew {a.topic} v{e['version']}")


def cmd_leave(a):
    _append(a.log, {"kind": "leave", "agent": a.agent})
    print(f"{a.agent} left; later commits no longer wait for {a.agent}")


def cmd_deviate(a):
    c = committed_value(a.log, a.topic)
    _append(a.log, {"kind": "deviate", "agent": a.agent, "topic": a.topic,
                    "version": c["version"] if c else None, "why": a.why})
    print(f"deviation announced on {a.topic}")


# ---------------------------------------------------------------- CLI
def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--log", default=os.environ.get("AGREE_LOG", "agreement_log.jsonl"))
    p.add_argument("--agent", default=os.environ.get("AGENT_ID", "agent"))
    s = p.add_subparsers(dest="cmd", required=True)
    x = s.add_parser("init"); x.add_argument("--participants", required=True); x.set_defaults(f=cmd_init)
    x = s.add_parser("propose"); x.add_argument("topic"); x.add_argument("value"); x.add_argument("--why", default=""); x.set_defaults(f=cmd_propose)
    x = s.add_parser("respond"); x.add_argument("topic"); x.add_argument("vote", choices=["accept", "object"]); x.add_argument("--why", default=""); x.set_defaults(f=cmd_respond)
    x = s.add_parser("commit"); x.add_argument("topic"); x.set_defaults(f=cmd_commit)
    x = s.add_parser("lookup"); x.add_argument("topic"); x.set_defaults(f=cmd_lookup)
    x = s.add_parser("status"); x.add_argument("topic", nargs="?"); x.set_defaults(f=cmd_status)
    x = s.add_parser("checker"); x.add_argument("topic"); x.add_argument("command"); x.set_defaults(f=cmd_checker)
    x = s.add_parser("check"); x.add_argument("topic"); x.add_argument("output"); x.set_defaults(f=cmd_check)
    x = s.add_parser("withdraw"); x.add_argument("topic"); x.add_argument("--why", default=""); x.set_defaults(f=cmd_withdraw)
    x = s.add_parser("leave"); x.set_defaults(f=cmd_leave)
    x = s.add_parser("deviate"); x.add_argument("topic"); x.add_argument("--why", required=True); x.set_defaults(f=cmd_deviate)
    a = p.parse_args()
    a.f(a)


if __name__ == "__main__":
    main()
