"""Tax module. Owned by agent2. Computes sales tax. The data files and rules are in data_tax/ next to this file.

API (committed shared decision `tax_api` v2):
- Money is int cents everywhere (inputs and return values).
- Percentages are percent numbers (8.25 means 8.25%; discount 10 means 10%).
- compute_tax(lines, region, discount_pct) -> int cents.
- rate_percent(region) -> Decimal percent.
- Unknown customer: pass region=None -> 0 tax.
- Unknown non-None region -> KeyError.
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
    exempt = set()
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            category = (row.get("category") or "").strip()
            if category:
                exempt.add(category)
    return exempt


_RATES = _load_rates(os.path.join(_DATA_DIR, "rates.csv"))
_EXEMPT_CATEGORIES = _load_exempt_categories(os.path.join(_DATA_DIR, "exempt_categories.csv"))


def rate_percent(region):
    """Return the sales tax rate for a region as a Decimal percent (e.g. Decimal('8.25')).

    region=None (unknown customer) -> Decimal('0').
    An unknown region code raises KeyError.
    """
    if region is None:
        return Decimal("0")
    return _RATES[region]


def compute_tax(lines, region, discount_pct):
    """Return the sales tax for an order in integer cents (rounded half up to the cent).

    lines: iterable of {"category": str, "amount_cents": int} (line amounts before discount).
           Lines whose category is in exempt_categories.csv are not taxed.
    region: customer region code (key of rates.csv), or None for an unknown customer (tax 0).
    discount_pct: customer discount as a percent number (10 means 10%); 0 if none.

    base = taxable_sum * (100 - discount_pct) / 100
    tax  = base * rate_pct / 100, rounded half up to the cent.
    """
    if region is None:
        return 0

    rate = rate_percent(region)  # raises KeyError for unknown region

    taxable_cents = 0
    for line in lines:
        amount = line["amount_cents"]
        if isinstance(amount, bool) or not isinstance(amount, int):
            raise TypeError(f"amount_cents must be int cents, got {type(amount).__name__}")
        if line["category"] in _EXEMPT_CATEGORIES:
            continue
        taxable_cents += amount

    discount = Decimal(str(discount_pct))
    base = Decimal(taxable_cents) * (Decimal(100) - discount) / Decimal(100)
    tax = base * rate / Decimal(100)
    return int(tax.quantize(Decimal("1"), rounding=ROUND_HALF_UP))
