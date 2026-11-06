"""Tax module. Owned by agent2. Computes sales tax.

The data files and rules are in data_tax/ next to this file:
  - rates.csv              region -> tax percent
  - exempt_categories.csv  categories that are not taxed
  - RULES.md               the tax rules

Conventions (team standard):
  - Money amounts are integers in cents (1250 means $12.50).
  - Percentages are percent numbers (10% is 10, 8.25% is 8.25).
  - A lookup that finds nothing raises KeyError.

Public API (agreed as topic "tax_api"):
  compute_tax(lines, region, discount_pct=0) -> int   sales tax in cents
  tax_pct(region) -> float                            rate in percent
  is_exempt(category) -> bool
"""

import csv
import os
from decimal import Decimal, ROUND_HALF_UP
from typing import Iterable, Optional, Tuple

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_tax")


def _load_rates(path: str) -> dict:
    rates = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            region = row["region"].strip()
            # Keep the exact decimal from the CSV (e.g. "8.875") to avoid float error.
            rates[region] = Decimal(row["tax_pct"].strip())
    return rates


def _load_exempt(path: str) -> frozenset:
    with open(path, newline="", encoding="utf-8") as f:
        return frozenset(
            row["category"].strip() for row in csv.DictReader(f) if row["category"].strip()
        )


_RATES = _load_rates(os.path.join(_DATA_DIR, "rates.csv"))
_EXEMPT = _load_exempt(os.path.join(_DATA_DIR, "exempt_categories.csv"))


def is_exempt(category: str) -> bool:
    """True if items in this category are not taxed (listed in exempt_categories.csv)."""
    return category in _EXEMPT


def _rate(region: Optional[str]) -> Decimal:
    """Tax rate in percent as Decimal. None (unknown customer) pays 0%.

    A region code that is not in rates.csv raises KeyError (team standard).
    """
    if region is None:
        return Decimal(0)
    return _RATES[region]


def tax_pct(region: Optional[str]) -> float:
    """Tax rate in percent for a region. None (unknown customer) -> 0.0.

    Raises KeyError if the region is not in rates.csv.
    """
    return float(_rate(region))


def compute_tax(
    lines: Iterable[Tuple[str, int]],
    region: Optional[str],
    discount_pct=0,
) -> int:
    """Return the sales tax in integer cents.

    lines        : iterable of (category, amount_cents) pairs for each line item.
                   Lines whose category is exempt are not taxed.
    region       : customer's region code (e.g. "TX"), or None for an unknown
                   customer, who pays 0% tax.
    discount_pct : customer's discount in percent (e.g. 10 for 10%). It is applied
                   to the taxable amount only.

    Rule (data_tax/RULES.md):
      taxable = sum of taxable line amounts
      base    = taxable * (100 - discount_pct) / 100
      tax     = base * tax_pct / 100, rounded to the cent (half up)
    The rounding happens once, on the final tax.
    """
    taxable = 0
    for category, amount_cents in lines:
        if isinstance(amount_cents, bool) or not isinstance(amount_cents, int):
            raise TypeError("amount_cents must be an int (cents), got %r" % (amount_cents,))
        if amount_cents < 0:
            raise ValueError("amount_cents must not be negative, got %r" % (amount_cents,))
        if not is_exempt(category):
            taxable += amount_cents

    if isinstance(discount_pct, bool) or not isinstance(discount_pct, (int, float, Decimal)):
        raise TypeError("discount_pct must be a number, got %r" % (discount_pct,))
    discount = Decimal(str(discount_pct))
    if not (Decimal(0) <= discount <= Decimal(100)):
        raise ValueError("discount_pct must be between 0 and 100, got %r" % (discount_pct,))

    rate = _rate(region)  # KeyError for an unknown region

    base = Decimal(taxable) * (Decimal(100) - discount) / Decimal(100)
    tax = base * rate / Decimal(100)
    return int(tax.quantize(Decimal(1), rounding=ROUND_HALF_UP))
