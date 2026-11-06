#!/usr/bin/env python3
"""Shared message board between teammates (available in every condition).

  msg.py send "text"        post a message to your teammates
  msg.py read               show all messages delivered so far (yours are marked with '>')
  msg.py wait [SECONDS]     block until a new message from a teammate arrives (default 60s)

If $MSG_DELAY_MIN/$MSG_DELAY_MAX are set (seconds), each message is delivered to the others only after a random
delay in that range, like a slow network. The sender always sees its own messages at once.
"""
import fcntl, json, os, random, sys, time

BOARD = os.environ["MSG_BOARD"]
ME = os.environ["AGENT_ID"]
DMIN = float(os.environ.get("MSG_DELAY_MIN", 0))
DMAX = float(os.environ.get("MSG_DELAY_MAX", 0))


def _all():
    if not os.path.exists(BOARD):
        return []
    with open(BOARD) as f:
        return [json.loads(l) for l in f if l.strip()]


def _visible():
    now = time.time()
    return [m for m in _all() if m["from"] == ME or m.get("deliver_at", m["ts"]) <= now]


def send(text):
    now = time.time()
    delay = random.uniform(DMIN, DMAX) if DMAX > 0 else 0
    with open(BOARD, "a") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        f.write(json.dumps({"from": ME, "ts": now, "deliver_at": now + delay, "text": text}, ensure_ascii=False) + "\n")
        fcntl.flock(f, fcntl.LOCK_UN)
    print("sent")


def read():
    ms = _visible()
    for m in ms:
        print(("> " if m["from"] == ME else "  ") + f"[{m['from']}] {m['text']}")
    if not ms:
        print("(no messages)")


def wait(sec):
    seen = len([m for m in _visible() if m["from"] != ME])
    end = time.time() + sec
    while time.time() < end:
        others = [m for m in _visible() if m["from"] != ME]
        if len(others) > seen:
            for m in others[seen:]:
                print(f"[{m['from']}] {m['text']}")
            return
        time.sleep(2)
    print("(no new message)")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "read"
    if cmd == "send":
        send(" ".join(sys.argv[2:]))
    elif cmd == "wait":
        wait(float(sys.argv[2]) if len(sys.argv) > 2 else 60)
    else:
        read()
