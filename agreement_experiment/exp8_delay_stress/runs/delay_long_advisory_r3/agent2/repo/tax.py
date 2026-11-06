"""Tax module. Owned by agent2. Computes sales tax. The data files and rules are in data_tax/ next to this file.

Committed interface (tax_api v4):
    compute_tax(region, discount_pct, lines) -> int   # sales tax in integer cents
    tax_pct(region) -> float                          # tax rate in percent (8.25 means 8.25%)

    region       : str code as in rates.csv (TX, NY, OR), or None for an unknown customer (tax 0)
    discount_pct : number, percent 0-100 (10 means 10%)
    lines        : list of {"category": str, "amount_cents": int}
                   amount_cents is the line total (qty x unit price), already computed by pricing.
"""

import csv
import os
from decimal import Decimal, ROUND_HALF_UP

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_tax")


def _load_rates(path):
    rates = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            region = row["region"].strip()
            rates[region] = Decimal(row["tax_pct"].strip())
    return rates


def _load_exempt_categories(path):
    with open(path, newline="", encoding="utf-8") as f:
        return {row["category"].strip() for row in csv.DictReader(f) if row["category"].strip()}


_RATES = _load_rates(os.path.join(_DATA_DIR, "rates.csv"))
_EXEMPT = _load_exempt_categories(os.path.join(_DATA_DIR, "exempt_categories.csv"))


def tax_pct(region):
    """Return the sales tax rate for `region` in percent (e.g. 8.25 for TX, 0 for OR).

    Raises KeyError if the region is not listed in rates.csv (None included).
    """
    return float(_RATES[region])


def compute_tax(region, discount_pct, lines):
    """Return the sales tax for an order in integer cents, rounded half up.

    Rules (data_tax/RULES.md):
      taxable_amount = sum of line amounts whose category is not exempt
      base           = taxable_amount * (100 - discount_pct) / 100
      tax            = base * tax_pct / 100, rounded to the cent (half up)
      unknown customer (region None) pays 0 tax.
    """
    if region is None:
        return 0

    rate = _RATES[region]  # KeyError on unknown region (tax lookup miss)

    discount = Decimal(str(discount_pct))
    if discount < 0 or discount > 100:
        raise ValueError(f"discount_pct must be between 0 and 100, got {discount_pct!r}")

    taxable_cents = 0
    for line in lines:
        if line["category"].strip() in _EXEMPT:
            continue
        taxable_cents += int(line["amount_cents"])

    base = Decimal(taxable_cents) * (Decimal(100) - discount) / Decimal(100)
    tax = base * rate / Decimal(100)
    return int(tax.quantize(Decimal("1"), rounding=ROUND_HALF_UP))
