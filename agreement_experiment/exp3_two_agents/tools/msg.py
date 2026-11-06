#!/usr/bin/env python3
"""Shared message board between teammates (available in every condition).

  msg.py send "text"        post a message to your teammate
  msg.py read               show all messages (mark yours with '>')
  msg.py wait [SECONDS]     block until a new message from your teammate arrives (default 60s)
"""
import fcntl, json, os, sys, time

BOARD = os.environ["MSG_BOARD"]
ME = os.environ["AGENT_ID"]


def _all():
    if not os.path.exists(BOARD):
        return []
    with open(BOARD) as f:
        return [json.loads(l) for l in f if l.strip()]


def send(text):
    with open(BOARD, "a") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        f.write(json.dumps({"from": ME, "ts": time.time(), "text": text}, ensure_ascii=False) + "\n")
        fcntl.flock(f, fcntl.LOCK_UN)
    print("sent")


def read():
    for m in _all():
        print(("> " if m["from"] == ME else "  ") + f"[{m['from']}] {m['text']}")
    if not _all():
        print("(no messages)")


def wait(sec):
    seen = len([m for m in _all() if m["from"] != ME])
    end = time.time() + sec
    while time.time() < end:
        others = [m for m in _all() if m["from"] != ME]
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
