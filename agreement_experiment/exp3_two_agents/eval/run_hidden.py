#!/usr/bin/env python3
"""Put agent1's pricing.py (with its data/) and agent2's invoice.py together and run hidden orders.
usage: run_hidden.py PRICING_PY INVOICE_PY [--example-only]   (prints JSON)"""
import json, os, shutil, subprocess, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from reference import render, EXAMPLE, HIDDEN, D  # noqa: E402

RUNNER = r'''
import json, sys
sys.path.insert(0, ".")
res = []
try:
    import invoice
except Exception as e:
    print(json.dumps({"import_error": "%s: %s" % (type(e).__name__, e)})); sys.exit(0)
for o in json.load(open("orders.json")):
    try:
        out = invoice.render_invoice(o)
    except Exception as e:
        out = "EXCEPTION: %s: %s" % (type(e).__name__, e)
    res.append(str(out))
print(json.dumps(res))
'''


def cases(example_only=False):
    cs = [("example", EXAMPLE)]
    if not example_only:
        cs += [(g, o) for g, os_ in HIDDEN.items() for o in os_]
    return cs


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
        res = json.loads(r.stdout.strip().splitlines()[-1])
        if isinstance(res, dict):
            return None, res["import_error"]
        return res, ""
    except Exception as e:  # noqa: BLE001
        return None, str(e)
    finally:
        shutil.rmtree(d, ignore_errors=True)


def evaluate(pricing_py, invoice_py, example_only=False):
    cs = cases(example_only)
    if not (os.path.exists(pricing_py) and os.path.exists(invoice_py)):
        return {"passed": 0, "total": len(cs), "error": "missing file", "cases": []}
    res, err = run(pricing_py, invoice_py, [o for _, o in cs])
    if res is None:
        return {"passed": 0, "total": len(cs), "error": err, "cases": []}
    out = []
    for (g, o), got in zip(cs, res):
        want = render(o)
        out.append({"group": g, "ok": got.strip() == want.strip(), "got": got, "want": want})
    return {"passed": sum(c["ok"] for c in out), "total": len(out), "error": "", "cases": out}


if __name__ == "__main__":
    r = evaluate(sys.argv[1], sys.argv[2], "--example-only" in sys.argv)
    print(json.dumps(r, ensure_ascii=False))
