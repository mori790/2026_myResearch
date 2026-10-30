"""Reference invoice (evaluator only). Prices in Decimal, round half up to cents."""
import csv, os
from decimal import Decimal, ROUND_HALF_UP
D = os.path.join(os.path.dirname(__file__), "..", "repo_template", "data")
CAT = {r["sku"]: r for r in csv.DictReader(open(os.path.join(D, "catalog.csv")))}
CUS = {r["id"]: r for r in csv.DictReader(open(os.path.join(D, "customers.csv")))}
c2 = lambda x: x.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
def render(order):
    cus = CUS.get(order["customer"])
    name = cus["name"] if cus else order["customer"]
    pct = int(cus["discount"].rstrip("%")) if cus else 0
    out, sub = [f"Customer: {name}"], Decimal("0")
    for sku, qty in order["lines"]:
        if sku not in CAT:
            out.append(f"UNKNOWN SKU: {sku}"); continue
        p = Decimal(CAT[sku]["price"]); amt = c2(p * qty); sub += amt
        out.append(f"{sku} x{qty} @ ${p:.2f} = ${amt:.2f}")
    disc = c2(sub * pct / 100)
    out += [f"Subtotal: ${sub:.2f}", f"Discount ({pct}%): -${disc:.2f}", f"Total: ${c2(sub - disc):.2f}"]
    return "\n".join(out)
EXAMPLE = {"customer": "C1", "lines": [["A", 2], ["Z", 1]]}
HIDDEN = [
    {"customer": "C1", "lines": [["A", 3], ["B", 4]]},
    {"customer": "C2", "lines": [["C", 1], ["E", 7]]},
    {"customer": "C3", "lines": [["D", 3], ["Q", 2], ["B", 1]]},
    {"customer": "C4", "lines": [["E", 3], ["D", 1]]},
    {"customer": "C9", "lines": [["A", 1]]},
    {"customer": "C3", "lines": [["X", 1], ["Y", 2]]},
]
if __name__ == "__main__":
    print(render(EXAMPLE)); print(); [print(render(o), end="\n\n") for o in HIDDEN]
