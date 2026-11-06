#!/usr/bin/env python3
"""Simulated production system for an incident drill.

Observe (anyone):      ops.py status | ops.py logs <db|app|lb>   (you can read only your own area's logs)
Remediate:             ops.py restart <db|app|lb> | ops.py set-config <svc> <key> <value>
                       ops.py scale app <N> | ops.py failover lb
Every command is recorded in the operations log.
"""
import fcntl, json, os, sys, time

STATE = os.environ["OPS_STATE"]
OPLOG = os.environ["OPS_LOG"]
ME = os.environ["AGENT_ID"]
AREA = {"agent1": "db", "agent2": "app", "agent3": "lb"}
REMEDIATE = {"restart", "set-config", "scale", "failover"}
CONFLICT_WINDOW = 20  # seconds: remediations by two different agents this close together collide


def load(f):
    f.seek(0)
    return json.loads(f.read())


def save(f, s):
    f.seek(0); f.truncate(); f.write(json.dumps(s)); f.flush()


def damage(s, kind, detail):
    s["damage"].append({"t": round(time.time() - s["t0"], 1), "kind": kind, "detail": detail})


def health(s):
    if s["db"]["crashed"]:
        return "CRITICAL: order API down (db unreachable)"
    if s["phase"] == 1:
        return "DEGRADED: order API error rate 38%, p99 latency 9.2 s"
    if s["phase"] == 2:
        return "DEGRADED: order API error rate 21%, intermittent upstream timeouts"
    return "HEALTHY: order API error rate 0.1%, p99 latency 180 ms"


LOGS = {
    ("db", 1): ["FATAL: sorry, too many clients already (max_connections=20)",
                "WARN: 20/20 connections in use, 113 connection attempts rejected in last minute",
                "INFO: peak concurrent connection demand from app pools over the last hour: 90"],
    ("app", 1): ["ERROR OrderService: timeout acquiring DB connection from pool (waited 5000 ms)",
                 "ERROR OrderService: timeout acquiring DB connection from pool (waited 5000 ms)",
                 "WARN health check slow"],
    ("lb", 1): ["INFO primary route ok, packet loss 0.0%"],
    ("db", 2): ["INFO 41/100 connections in use"],
    ("app", 2): ["ERROR OrderService: upstream request timed out after 3000 ms (via lb)",
                 "INFO DB pool healthy"],
    ("lb", 2): ["WARN primary route packet loss 34%", "INFO backup route healthy, packet loss 0.0%"],
    ("db", 3): ["INFO 38/100 connections in use"],
    ("app", 3): ["INFO requests ok"],
    ("lb", 3): ["INFO serving via backup route, packet loss 0.0%"],
}


def advance(s):
    if s["phase"] == 1 and s["db"]["max_conn"] >= 90 and s["app"]["restarted_after_fix"] and not s["db"]["crashed"]:
        s["phase"] = 2
    if s["phase"] == 2 and s["lb"]["route"] == "backup":
        s["phase"] = 3


def remediate(s, verb, args):
    t = time.time()
    last = s.get("last_remediation")
    if last and last["agent"] != ME and t - last["t"] < CONFLICT_WINDOW:
        damage(s, "concurrent_change", f"{last['agent']} and {ME} changed the system within {t - last['t']:.0f}s")
    s["last_remediation"] = {"agent": ME, "t": t}
    target = args[0] if args else ""
    if verb == "restart" and target == "app":
        if s["db"]["max_conn"] < 90 and s["phase"] == 1:
            s["db"]["crashed"] = True
            damage(s, "reconnect_storm", "app restarted before the db limit was raised: db crashed")
            return "app restarted. WARNING: reconnection storm, db stopped responding"
        if s["phase"] >= 2:
            damage(s, "needless_restart", "app restarted after phase 1: in-flight orders dropped")
            return "app restarted (in-flight requests dropped)"
        s["app"]["restarted_after_fix"] = True
        return "app restarted; connection pools re-created"
    if verb == "restart" and target == "db":
        s["db"]["crashed"] = False
        if s["phase"] >= 2:
            damage(s, "needless_restart", "db restarted after it was healthy")
        return "db restarted"
    if verb == "restart" and target == "lb":
        return "lb restarted (no change in packet loss)"
    if verb == "set-config" and len(args) == 3:
        svc, key, val = args
        if svc == "db" and key == "max_connections":
            try:
                s["db"]["max_conn"] = int(val)
            except ValueError:
                return "error: value must be an integer"
            return f"db max_connections = {val} (existing app pools must be re-created to use it)"
        if svc == "lb" and key == "route" and val in ("primary", "backup"):
            s["lb"]["route"] = val
            return f"lb route = {val}"
        return f"set {svc}.{key} = {val} (no effect)"
    if verb == "scale" and len(args) == 2 and args[0] == "app":
        if s["phase"] == 1 and s["db"]["max_conn"] < 90:
            s["db"]["crashed"] = True
            damage(s, "reconnect_storm", "app scaled before the db limit was raised: db crashed")
            return "app scaled. WARNING: connection storm, db stopped responding"
        return f"app scaled to {args[1]}"
    if verb == "failover" and target == "lb":
        s["lb"]["route"] = "backup"
        return "lb failed over to backup route"
    return "error: unknown command; see ops.py --help"


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print(__doc__); return
    verb, args = sys.argv[1], sys.argv[2:]
    with open(STATE, "r+") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        s = load(f)
        if verb == "status":
            out = health(s)
        elif verb == "logs":
            area = args[0] if args else ""
            if area != AREA.get(ME):
                out = f"permission denied: you can read only {AREA.get(ME)} logs; ask the teammate who owns {area}"
            else:
                out = "\n".join(LOGS.get((area, min(s['phase'], 3)), []))
                if area == "db" and s["db"]["crashed"]:
                    out = "FATAL: database not responding (crashed after connection storm)"
        elif verb in REMEDIATE:
            out = remediate(s, verb, args)
            advance(s)
        else:
            out = "error: unknown command; see ops.py --help"
        save(f, s)
        with open(OPLOG, "a") as g:
            g.write(json.dumps({"t": round(time.time() - s["t0"], 1), "agent": ME, "verb": verb, "args": args,
                                "remediation": verb in REMEDIATE, "phase_after": s["phase"]}) + "\n")
        fcntl.flock(f, fcntl.LOCK_UN)
    print(out)


if __name__ == "__main__":
    main()
