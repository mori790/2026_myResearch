"""Reference invoice renderer and hidden test orders, grouped by the shared choice they exercise."""
import csv, os
from decimal import Decimal, ROUND_HALF_UP

D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "repo1", "data")
CENT = Decimal("0.01")


def _load():
    cat = {r["sku"]: r for r in csv.DictReader(open(os.path.join(D, "catalog.csv")))}
    cus = {r["id"]: r for r in csv.DictReader(open(os.path.join(D, "customers.csv")))}
    tax = {r["region"]: r for r in csv.DictReader(open(os.path.join(D, "tax.csv")))}
    return cat, cus, tax


def pct(x):
    s = format(Decimal(x).normalize(), "f")
    return s


def money(x):
    return "$" + format(x.quantize(CENT, ROUND_HALF_UP), "f")


def render(order):
    cat, cus, tax = _load()
    c = cus.get(order["customer"])
    name = c["name"] if c else order["customer"]
    disc = Decimal(c["discount_pct"]) if c else Decimal(0)
    trate = Decimal(tax[c["region"]]["tax_pct"]) if c else Decimal(0)
    out = [f"Customer: {name}"]
    sub = Decimal(0)
    for sku, q in order["lines"]:
        if sku not in cat:
            out.append(f"UNKNOWN SKU: {sku}")
            continue
        unit = Decimal(cat[sku]["price_cents"]) / 100
        amt = unit * q
        sub += amt
        out.append(f"{sku} x{q} @ {money(unit)} = {money(amt)}")
    d = (sub * disc / 100).quantize(CENT, ROUND_HALF_UP)
    t = ((sub - d) * trate / 100).quantize(CENT, ROUND_HALF_UP)
    out += [f"Subtotal: {money(sub)}", f"Discount ({pct(disc)}%): -{money(d)}",
            f"Tax ({pct(trate)}%): {money(t)}", f"Total: {money(sub - d + t)}"]
    return "\n".join(out)


EXAMPLE = {"customer": "C1", "lines": [["A", 2], ["Z", 1]]}

# Each group isolates one shared choice as far as possible.
HIDDEN = {
    "basic":    [{"customer": "C2", "lines": [["A", 1], ["B", 3]]},
                 {"customer": "C2", "lines": [["C", 2], ["D", 1], ["E", 4]]}],
    "unknown":  [{"customer": "C2", "lines": [["B", 2], ["X", 1]]},
                 {"customer": "C2", "lines": [["Q", 3], ["D", 2]]}],
    "discount": [{"customer": "C5", "lines": [["C", 1], ["B", 2]]},
                 {"customer": "C5", "lines": [["A", 3], ["E", 2]]}],
    "tax":      [{"customer": "C4", "lines": [["D", 2], ["B", 1]]},
                 {"customer": "C4", "lines": [["C", 1], ["E", 3]]}],
    "unknown_customer": [{"customer": "C9", "lines": [["A", 1]]}],
    "combined": [{"customer": "C3", "lines": [["A", 1], ["C", 1], ["Y", 2]]},
                 {"customer": "C1", "lines": [["D", 3], ["E", 1], ["Z", 1]]}],
}

if __name__ == "__main__":
    print(render(EXAMPLE))
    for g, os_ in HIDDEN.items():
        for o in os_:
            print("--", g); print(render(o))
