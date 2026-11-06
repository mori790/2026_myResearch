"""Tax module. Owned by agent2. Computes sales tax. The data files and rules are in data_tax/ next to this file.

Implements the committed decision `tax_interface` (v3):
  - money: float dollars in and out; all arithmetic is done in Decimal internally
  - percentages: fractions (0.0825 = 8.25%)
  - compute_tax(lines, region, discount=0.0) -> float dollars, rounded to the cent (ROUND_HALF_UP)
  - tax_rate(region) -> float fraction
  - is_exempt(category) -> bool
  - unknown non-None region -> KeyError; region None (unknown customer) -> 0
  - unknown category -> taxable

This module does not look up SKUs or customers. The caller passes categories, amounts, region and discount.
"""

import csv
import os
from decimal import Decimal, ROUND_HALF_UP

__all__ = ["compute_tax", "tax_rate", "is_exempt"]

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_tax")
_CENT = Decimal("0.01")
_HUNDRED = Decimal(100)


def _load_rates():
    """Return {region: Decimal fraction} from rates.csv (tax_pct is a percent number)."""
    rates = {}
    path = os.path.join(_DATA_DIR, "rates.csv")
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            region = row["region"].strip()
            rates[region] = Decimal(row["tax_pct"].strip()) / _HUNDRED
    return rates


def _load_exempt_categories():
    """Return the set of exempt categories (casefolded) from exempt_categories.csv."""
    exempt = set()
    path = os.path.join(_DATA_DIR, "exempt_categories.csv")
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            name = row["category"].strip()
            if name:
                exempt.add(name.casefold())
    return exempt


_RATES = _load_rates()
_EXEMPT = _load_exempt_categories()


def _rate_decimal(region):
    """Tax rate as a Decimal fraction. None (unknown customer) -> 0. Unknown region -> KeyError."""
    if region is None:
        return Decimal(0)
    key = str(region).strip()
    if key not in _RATES:
        raise KeyError(f"unknown tax region: {region!r}")
    return _RATES[key]


def is_exempt(category):
    """True if the category is listed in exempt_categories.csv. Unknown categories are taxable."""
    return str(category).strip().casefold() in _EXEMPT


def tax_rate(region):
    """Tax rate for a region as a float fraction (0.0825 for TX). None -> 0.0.

    Raises KeyError if the region is not in rates.csv.
    """
    return float(_rate_decimal(region))


def compute_tax(lines, region, discount=0.0):
    """Compute sales tax for an order.

    lines:    iterable of (category, amount) pairs for all line items, amount in float dollars,
              before discount.
    region:   customer region code, or None for an unknown customer (tax is 0).
    discount: customer discount as a fraction (0.10 = 10%). None is treated as 0.

    Rule (RULES.md):
      taxable_sum = sum of amounts whose category is not exempt
      base        = taxable_sum * (1 - discount)
      tax         = base * tax_rate, rounded to the cent, half up (computed once at the end)

    Returns float dollars.
    """
    if discount is None:
        discount = 0.0
    d = Decimal(str(discount))
    if d < 0 or d > 1:
        raise ValueError(f"discount must be a fraction between 0 and 1, got {discount!r}")

    taxable = Decimal(0)
    for category, amount in lines:
        if not is_exempt(category):
            taxable += Decimal(str(amount))

    base = taxable * (Decimal(1) - d)
    tax = base * _rate_decimal(region)
    return float(tax.quantize(_CENT, rounding=ROUND_HALF_UP))
