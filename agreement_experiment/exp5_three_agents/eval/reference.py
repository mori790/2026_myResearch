"""Reference renderer and hidden orders for the 3-agent task, grouped by the shared choice they exercise."""
import csv, os
from decimal import Decimal, ROUND_HALF_UP
HERE = os.path.dirname(os.path.abspath(__file__))
DP = os.path.join(HERE, "..", "repo1", "data_pricing")
DT = os.path.join(HERE, "..", "repo2", "data_tax")
CENT = Decimal("0.01")


def _csv(d, f):
    return list(csv.DictReader(open(os.path.join(d, f))))


def money(x):
    return "$" + format(x.quantize(CENT, ROUND_HALF_UP), "f")


def pct(x):
    return format(Decimal(x).normalize(), "f")


def render(order):
    cat = {r["sku"]: r for r in _csv(DP, "catalog.csv")}
    cus = {r["id"]: r for r in _csv(DP, "customers.csv")}
    rates = {r["region"]: r["tax_pct"] for r in _csv(DT, "rates.csv")}
    exempt = {r["category"] for r in _csv(DT, "exempt_categories.csv")}
    c = cus.get(order["customer"])
    name = c["name"] if c else order["customer"]
    disc = Decimal(c["discount_pct"]) if c else Decimal(0)
    rate = Decimal(rates[c["region"]]) if c else Decimal(0)
    out, sub, taxable = [f"Customer: {name}"], Decimal(0), Decimal(0)
    for sku, q in order["lines"]:
        if sku not in cat:
            out.append(f"UNKNOWN SKU: {sku}")
            continue
        unit = Decimal(cat[sku]["price_cents"]) / 100
        amt = unit * q
        sub += amt
        if cat[sku]["category"] not in exempt:
            taxable += amt
        out.append(f"{sku} x{q} @ {money(unit)} = {money(amt)}")
    d = (sub * disc / 100).quantize(CENT, ROUND_HALF_UP)
    t = (taxable * (100 - disc) / 100 * rate / 100).quantize(CENT, ROUND_HALF_UP)
    out += [f"Subtotal: {money(sub)}", f"Discount ({pct(disc)}%): -{money(d)}",
            f"Tax ({pct(rate)}%): {money(t)}", f"Total: {money(sub - d + t)}"]
    return "\n".join(out)


EXAMPLE = {"customer": "C1", "lines": [["A", 2], ["D", 2], ["Z", 1]]}
HIDDEN = {
    "basic":    [{"customer": "C2", "lines": [["A", 1], ["B", 3]]},
                 {"customer": "C2", "lines": [["C", 2], ["E", 4]]}],
    "unknown":  [{"customer": "C2", "lines": [["B", 2], ["X", 1]]},
                 {"customer": "C2", "lines": [["Q", 3], ["C", 1]]}],
    "discount": [{"customer": "C5", "lines": [["C", 1], ["B", 2]]},
                 {"customer": "C5", "lines": [["A", 3], ["E", 2]]}],
    "tax":      [{"customer": "C4", "lines": [["A", 1], ["B", 1]]},
                 {"customer": "C4", "lines": [["C", 1], ["E", 3]]}],
    "exempt":   [{"customer": "C4", "lines": [["D", 2], ["B", 1]]},
                 {"customer": "C4", "lines": [["F", 3], ["C", 1], ["D", 1]]}],
    "unknown_customer": [{"customer": "C9", "lines": [["A", 1], ["D", 1]]}],
    "combined": [{"customer": "C3", "lines": [["A", 1], ["D", 2], ["Y", 2]]},
                 {"customer": "C1", "lines": [["F", 3], ["E", 1], ["C", 1], ["Z", 1]]}],
}

if __name__ == "__main__":
    for g, os_ in [("example", [EXAMPLE])] + list(HIDDEN.items()):
        for o in os_:
            print("--", g); print(render(o))
