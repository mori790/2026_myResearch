"""Tax module. Owned by agent2. Computes sales tax.

The data files and rules are in data_tax/ next to this file:
  - data_tax/rates.csv              region -> tax_pct (percent number, e.g. 8.25)
  - data_tax/exempt_categories.csv  categories that are not taxed
  - data_tax/RULES.md               the tax rules

Conventions (team standard):
  - Money amounts are integers in cents (1250 means $12.50).
  - Percentages are percent numbers (10% is 10, 8.25% is 8.25).
  - A lookup that finds nothing raises KeyError.
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
            # Keep the exact decimal text from the file to avoid float error.
            rates[region] = Decimal(row["tax_pct"].strip())
    return rates


def _load_exempt(path):
    with open(path, newline="", encoding="utf-8") as f:
        return {row["category"].strip() for row in csv.DictReader(f) if row["category"].strip()}


_RATES = _load_rates(os.path.join(_DATA_DIR, "rates.csv"))
_EXEMPT = _load_exempt(os.path.join(_DATA_DIR, "exempt_categories.csv"))


def tax_pct_for_region(region):
    """Return the tax percent (percent number, e.g. 8.25) for a region.

    Raises KeyError if the region is not listed in rates.csv.
    """
    return float(_RATES[region])


def is_exempt(category):
    """Return True if items in this category are not taxed."""
    return category in _EXEMPT


def compute_tax(lines, region, discount_pct=0):
    """Compute sales tax for an order, in integer cents.

    lines        : iterable of dicts {"amount_cents": int, "category": str}
    region       : customer region string (e.g. "TX"), or None for an
                   unknown customer, which pays 0 tax.
    discount_pct : customer discount as a percent number (e.g. 10 for 10%).

    Rules (data_tax/RULES.md):
      taxable = sum of amount_cents of non-exempt lines
      base    = taxable * (100 - discount_pct) / 100
      tax     = base * tax_pct / 100, rounded to the cent (half up)

    Raises KeyError for an unknown region string.
    Raises ValueError if discount_pct is outside [0, 100].
    """
    discount = Decimal(str(discount_pct))
    if discount < 0 or discount > 100:
        raise ValueError("discount_pct must be between 0 and 100, got %r" % (discount_pct,))

    taxable = 0
    for line in lines:
        if not is_exempt(line["category"]):
            taxable += int(line["amount_cents"])

    if region is None:
        return 0

    tax_pct = _RATES[region]  # KeyError if the region is unknown

    base = Decimal(taxable) * (Decimal(100) - discount) / Decimal(100)
    tax = base * tax_pct / Decimal(100)
    return int(tax.quantize(Decimal("1"), rounding=ROUND_HALF_UP))
