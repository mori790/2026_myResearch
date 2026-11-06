"""Tax module. Owned by agent2. Computes sales tax.

Data files and rules are in data_tax/ next to this file:
  - rates.csv               region -> tax_pct (percent number, e.g. 8.25)
  - exempt_categories.csv   categories that are not taxed
  - RULES.md                the tax rules

Team conventions (agreed in the shared log: tax.api, tax.rounding, tax.unknown):
  - Money amounts are integer cents (1250 == $12.50).
  - Percentages are percent numbers (8.25 == 8.25%).
  - A lookup that finds nothing raises KeyError.
  - Unknown customer (region=None) pays 0 tax, no error.
  - Arithmetic is exact (fractions.Fraction); the result is rounded once,
    half up, to the cent.

Public API:
  compute_tax(lines, region, discount_pct) -> int   tax in cents
  tax_rate(region) -> float                          percent number
  is_exempt(category) -> bool
"""

import csv
import math
import os
from fractions import Fraction

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_tax")


def _to_fraction(value):
    """Convert a percent/fraction number to an exact Fraction.

    Going through str() avoids binary float noise (e.g. 8.25 stays exactly 8.25),
    and limit_denominator snaps values such as 10.000000000000002 (from 0.1*100)
    back to 10.
    """
    return Fraction(str(value)).limit_denominator(1_000_000)


def _load_rates(path):
    rates = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            region = row["region"].strip()
            rates[region] = _to_fraction(row["tax_pct"].strip())
    return rates


def _load_exempt(path):
    exempt = set()
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            category = (row.get("category") or "").strip()
            if category:
                exempt.add(category)
    return exempt


_RATES = _load_rates(os.path.join(_DATA_DIR, "rates.csv"))
_EXEMPT = _load_exempt(os.path.join(_DATA_DIR, "exempt_categories.csv"))


def tax_rate(region):
    """Return the tax percent for a region (e.g. 'TX' -> 8.25).

    Raises KeyError if the region is not in rates.csv.
    """
    if region not in _RATES:
        raise KeyError(f"unknown tax region: {region!r}")
    return float(_RATES[region])


def is_exempt(category):
    """True if items in this category are not taxed (exempt_categories.csv)."""
    return category in _EXEMPT


def compute_tax(lines, region, discount_pct):
    """Compute sales tax for an order, in integer cents.

    lines        : iterable of (line_total_cents: int, category: str)
    region       : region string such as 'TX', or None for an unknown customer
                   (unknown customer pays 0 tax). An unknown region string
                   raises KeyError.
    discount_pct : customer discount as a percent number, 0..100 (0 if none)

    Rule (RULES.md):
      taxable = sum of line amounts whose category is not exempt
      base    = taxable * (100 - discount_pct) / 100
      tax     = base * tax_pct / 100, rounded to the cent (half up)
    """
    taxable = 0
    for amount_cents, category in lines:
        if isinstance(amount_cents, bool) or not isinstance(amount_cents, int):
            raise TypeError(
                f"line amount must be int cents, got {type(amount_cents).__name__}"
            )
        if not is_exempt(category):
            taxable += amount_cents

    discount = _to_fraction(discount_pct if discount_pct is not None else 0)
    if not (0 <= discount <= 100):
        raise ValueError(f"discount_pct must be between 0 and 100, got {discount_pct!r}")

    if region is None:
        # Unknown customer: 0% tax (RULES.md).
        return 0

    if region not in _RATES:
        raise KeyError(f"unknown tax region: {region!r}")
    rate = _RATES[region]

    base = Fraction(taxable) * (100 - discount) / 100
    tax = base * rate / 100

    # Round half up to the nearest cent. tax is non-negative here.
    return math.floor(tax + Fraction(1, 2))
