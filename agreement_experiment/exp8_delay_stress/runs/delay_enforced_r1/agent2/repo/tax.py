"""Tax module. Owned by agent2. Computes sales tax.

The data files and rules are in data_tax/ next to this file:
  - rates.csv                : region -> tax percent (e.g. TX -> 8.25)
  - exempt_categories.csv    : item categories that are not taxed
  - RULES.md                 : the tax rules

Shared conventions (committed in the team decision log):
  - Money amounts are int cents (1250 = $12.50).
  - Percentages are percent numbers (8.25 = 8.25%, 10 = 10%).
  - Results are int cents, rounded half-up to the cent.
  - An unknown customer (region None) pays 0 tax.
  - An unknown region (not in rates.csv) raises KeyError.

Public API:
  compute_tax(region, discount_pct, lines) -> int cents
  tax_pct(region) -> percent number
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


def _load_exempt(path):
    exempt = set()
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            category = row["category"].strip()
            if category:
                exempt.add(category)
    return exempt


_RATES = _load_rates(os.path.join(_DATA_DIR, "rates.csv"))
_EXEMPT_CATEGORIES = _load_exempt(os.path.join(_DATA_DIR, "exempt_categories.csv"))


def tax_pct(region):
    """Return the tax percent for a region, e.g. 8.25 for TX.

    region None (unknown customer) returns 0.
    A region not in rates.csv raises KeyError.
    """
    if region is None:
        return 0
    return _RATES[region]


def compute_tax(region, discount_pct, lines):
    """Return the sales tax in int cents for one order.

    region       : str such as "TX", or None for an unknown customer (tax is 0).
    discount_pct : customer discount as a percent number (10 = 10% off, 0 if none).
    lines        : iterable of (category, amount_cents) for every line item.
                   Items whose category is in exempt_categories.csv are not taxed.

    Rules (data_tax/RULES.md):
      taxable = sum of amount_cents for non-exempt lines
      base    = taxable * (100 - discount_pct) / 100
      tax     = base * tax_pct / 100, rounded half-up to the cent
    """
    if region is None:
        return 0

    rate = tax_pct(region)  # raises KeyError for an unknown region

    taxable = 0
    for category, amount_cents in lines:
        if category not in _EXEMPT_CATEGORIES:
            taxable += int(amount_cents)

    # Use Decimal for exact arithmetic (no float rounding drift).
    discount = Decimal(str(discount_pct))
    tax = Decimal(taxable) * (Decimal(100) - discount) * rate / Decimal(10000)
    return int(tax.quantize(Decimal("1"), rounding=ROUND_HALF_UP))
