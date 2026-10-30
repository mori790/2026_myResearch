"""Reference exclusion rules used by the evaluator (agents do NOT see this file)."""
import csv, statistics
def load(path):
    with open(path) as f:
        return [{"id": int(r["id"]), "group": r["group"], "rt": float(r["rt"])} for r in csv.DictReader(f)]
def excluded(rows, rule):
    x = [r["rt"] for r in rows]; k = float(rule["k"]); m = rule["method"]
    if m == "sd":
        mu, s = statistics.mean(x), statistics.pstdev(x)
        return sorted(r["id"] for r in rows if abs(r["rt"] - mu) > k * s)
    if m == "iqr":
        q1, _, q3 = statistics.quantiles(x, n=4); i = q3 - q1
        return sorted(r["id"] for r in rows if r["rt"] < q1 - k * i or r["rt"] > q3 + k * i)
    if m == "mad":
        med = statistics.median(x); mad = statistics.median(abs(v - med) for v in x) * 1.4826
        return sorted(r["id"] for r in rows if abs(r["rt"] - med) > k * mad)
    raise ValueError(f"unknown method {m}")
