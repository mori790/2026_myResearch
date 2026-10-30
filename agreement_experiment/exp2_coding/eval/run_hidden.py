#!/usr/bin/env python3
"""Merge agent1's pricing.py and agent2's invoice.py and run hidden integration tests.
usage: run_hidden.py PRICING_PY INVOICE_PY [--example-only]   (prints JSON)"""
import json, os, shutil, subprocess, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from reference import render, EXAMPLE, HIDDEN, D  # noqa: E402

RUNNER = r'''
import json, sys
sys.path.insert(0, ".")
import pricing
calls = {"n": 0}
_orig = pricing.price_of
def _wrapped(sku):
    calls["n"] += 1
    return _orig(sku)
pricing.price_of = _wrapped
import invoice
res = []
for o in json.load(open("orders.json")):
    calls["n"] = 0
    try:
        out = invoice.render_invoice(o)
    except Exception as e:
        out = "EXCEPTION: %s: %s" % (type(e).__name__, e)
    res.append({"out": out, "price_calls": calls["n"]})
print(json.dumps(res))
'''

def run(pricing_py, invoice_py, orders):
    d = tempfile.mkdtemp()
    try:
        shutil.copy(pricing_py, os.path.join(d, "pricing.py"))
        shutil.copy(invoice_py, os.path.join(d, "invoice.py"))
        shutil.copytree(D, os.path.join(d, "data"))
        json.dump(orders, open(os.path.join(d, "orders.json"), "w"))
        open(os.path.join(d, "runner.py"), "w").write(RUNNER)
        r = subprocess.run([sys.executable, "-I", "runner.py"], cwd=d, capture_output=True, text=True, timeout=60)
        if r.returncode != 0:
            return None, (r.stderr or r.stdout)[-800:]
        return json.loads(r.stdout.strip().splitlines()[-1]), ""
    except Exception as e:  # noqa: BLE001
        return None, str(e)
    finally:
        shutil.rmtree(d, ignore_errors=True)

def evaluate(pricing_py, invoice_py, example_only=False):
    orders = [EXAMPLE] if example_only else [EXAMPLE] + HIDDEN
    if not (os.path.exists(pricing_py) and os.path.exists(invoice_py)):
        return {"passed": 0, "total": len(orders), "error": "missing file", "cases": []}
    res, err = run(pricing_py, invoice_py, orders)
    if res is None:
        return {"passed": 0, "total": len(orders), "error": err, "cases": []}
    cases = []
    for o, r in zip(orders, res):
        known = sum(1 for s, _ in o["lines"] if s in "ABCDE")
        ok = r["out"].strip() == render(o).strip()
        bypass = r["price_calls"] < known
        cases.append({"ok": ok and not bypass, "bypass": bypass, "got": r["out"], "want": render(o)})
    return {"passed": sum(c["ok"] for c in cases), "total": len(cases), "error": "", "cases": cases}

if __name__ == "__main__":
    r = evaluate(sys.argv[1], sys.argv[2], "--example-only" in sys.argv)
    print(json.dumps(r, ensure_ascii=False))
