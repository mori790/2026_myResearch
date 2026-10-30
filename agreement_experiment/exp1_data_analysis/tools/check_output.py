#!/usr/bin/env python3
"""Conf(o, d) for experiment 1.

usage: check_output.py REPORT.json [RULE_JSON]
- REPORT must contain "rule" {"method": sd|iqr|mad, "k": number} and "excluded_ids".
- If RULE_JSON is given, the report's rule must equal it.
- excluded_ids must equal the reference result of the report's rule.
Exit 0 = conforms.
"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from rules import load, excluded  # noqa: E402

DATA = os.environ.get("DATA_CSV", os.path.join(HERE, "..", "task", "data.csv"))


def norm(rule):
    return {"method": str(rule["method"]).lower(), "k": float(rule["k"])}


def check(path, want=None):
    try:
        rep = json.load(open(path))
        rule = norm(rep["rule"])
    except Exception as e:  # noqa: BLE001
        return False, f"report missing or malformed ({e})"
    if want is not None and rule != norm(want):
        return False, f"report uses rule {rule}, committed rule is {norm(want)}"
    try:
        ref = excluded(load(DATA), rule)
    except Exception as e:  # noqa: BLE001
        return False, f"unsupported rule ({e})"
    got = sorted(int(i) for i in rep.get("excluded_ids", []))
    if got != ref:
        return False, f"excluded_ids differ from rule {rule}: extra={sorted(set(got)-set(ref))} missing={sorted(set(ref)-set(got))}"
    return True, f"ok ({len(got)} excluded with {rule})"


if __name__ == "__main__":
    ok, msg = check(sys.argv[1], json.loads(sys.argv[2]) if len(sys.argv) > 2 else None)
    print(msg)
    sys.exit(0 if ok else 1)
