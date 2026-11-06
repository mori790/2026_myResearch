"""Tax module. Owned by agent2. Computes sales tax.

The data files and rules are in data_tax/ next to this file.

Conventions (team standard):
  - Money amounts are integers in cents (1250 means $12.50).
  - Percentages are percent numbers (10 means 10%, 8.25 means 8.25%).
  - A lookup that finds nothing raises KeyError.

Public API:
  compute_tax(lines, region, discount_pct=0) -> int (cents)
  tax_pct_for_region(region) -> Decimal
  is_exempt(category) -> bool

  lines        : iterable of (category, amount_cents) pairs. amount_cents is an
                 int (the line total). category is a str.
  region       : region code string as used in rates.csv (e.g. "TX").
                 Pass None for an unknown customer -> 0% tax.
                 An unrecognised (non-None) region raises KeyError.
  discount_pct : customer's discount percent (e.g. 10 for 10%). Default 0.
"""

import csv
import os
from decimal import Decimal, ROUND_HALF_UP

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_tax")
_RATES_PATH = os.path.join(_DATA_DIR, "rates.csv")
_EXEMPT_PATH = os.path.join(_DATA_DIR, "exempt_categories.csv")


def _load_rates(path):
    rates = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            region = row["region"].strip()
            rates[region] = Decimal(row["tax_pct"].strip())
    return rates


def _load_exempt(path):
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return {row["category"].strip() for row in reader if row["category"].strip()}


_RATES = _load_rates(_RATES_PATH)
_EXEMPT = _load_exempt(_EXEMPT_PATH)


def tax_pct_for_region(region):
    """Return the tax percent (Decimal) for a region. Raises KeyError if unknown.

    None (unknown customer) returns 0.
    """
    if region is None:
        return Decimal(0)
    return _RATES[region]


def is_exempt(category):
    """True if items of this category are not taxed."""
    return category in _EXEMPT


def compute_tax(lines, region, discount_pct=0):
    """Compute sales tax in integer cents.

    Rules (data_tax/RULES.md):
      taxable_amount = sum of line amounts whose category is not exempt
      base = taxable_amount * (100 - discount_pct) / 100
      tax  = base * tax_pct / 100, rounded to the cent (half up)
    """
    taxable = 0
    for category, amount_cents in lines:
        if not is_exempt(category):
            taxable += int(amount_cents)

    discount = Decimal(str(discount_pct))
    if discount < 0 or discount > 100:
        raise ValueError("discount_pct must be between 0 and 100")

    tax_pct = tax_pct_for_region(region)

    base = Decimal(taxable) * (Decimal(100) - discount) / Decimal(100)
    tax = base * tax_pct / Decimal(100)
    return int(tax.quantize(Decimal("1"), rounding=ROUND_HALF_UP))
