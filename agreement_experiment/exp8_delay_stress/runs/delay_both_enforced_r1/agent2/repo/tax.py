"""Tax module. Owned by agent2. Computes sales tax.

The data files and rules are in data_tax/ next to this file:
  - data_tax/rates.csv              region -> tax percent
  - data_tax/exempt_categories.csv  categories that are not taxed
  - data_tax/RULES.md               the tax rules

Public API (committed decision 'module_api' v3):
  tax_rate(region) -> number
      Tax percent for the region (8.25 means 8.25%). Returns 0 if the region
      is None, empty, or not in rates.csv.
  is_exempt(category) -> bool
      True if the category is listed in exempt_categories.csv.
  tax_amount(region, discount_pct, lines) -> int
      Sales tax in integer cents, rounded half up once at the end.
      region       : customer's region code, or None for an unknown customer (0 tax).
      discount_pct : customer's discount as a percent number (10 means 10%).
      lines        : [(category, line_amount_cents), ...] for known items,
                     line_amount = unit_price_cents * qty, before discount.

Rules (data_tax/RULES.md):
  taxable = sum of line amounts whose category is not exempt
  base    = taxable * (100 - discount_pct) / 100
  tax     = base * tax_pct / 100, rounded to the cent (half up)

All arithmetic is exact (fractions); rounding happens once, at the end.
"""

import csv
import os
from fractions import Fraction
from functools import lru_cache

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_tax")
_RATES_PATH = os.path.join(_DATA_DIR, "rates.csv")
_EXEMPT_PATH = os.path.join(_DATA_DIR, "exempt_categories.csv")


@lru_cache(maxsize=None)
def _load_rates() -> dict:
    rates = {}
    with open(_RATES_PATH, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            region = row["region"].strip()
            if region:
                # Keep the exact decimal value (e.g. "8.875") as a Fraction.
                rates[region] = Fraction(row["tax_pct"].strip())
    return rates


@lru_cache(maxsize=None)
def _load_exempt() -> frozenset:
    with open(_EXEMPT_PATH, newline="", encoding="utf-8") as f:
        return frozenset(
            row["category"].strip()
            for row in csv.DictReader(f)
            if row["category"].strip()
        )


def _to_fraction(value) -> Fraction:
    """Convert a number to an exact Fraction using its decimal meaning.

    Fraction(str(x)) is used for floats so that 8.25 becomes exactly 825/100
    instead of the nearest binary float.
    """
    if isinstance(value, Fraction):
        return value
    if isinstance(value, int):
        return Fraction(value)
    return Fraction(str(value))


def tax_rate(region):
    """Return the tax percent for `region` (e.g. 8.25). 0 if unknown or empty."""
    if region is None:
        return 0
    key = str(region).strip()
    rates = _load_rates()
    if key not in rates:
        return 0
    rate = rates[key]
    return int(rate) if rate.denominator == 1 else float(rate)


def is_exempt(category) -> bool:
    """True if `category` is listed in exempt_categories.csv."""
    if category is None:
        return False
    return str(category).strip() in _load_exempt()


def _round_half_up(x: Fraction) -> int:
    """Round an exact Fraction to the nearest integer, ties away from zero."""
    if x >= 0:
        return (2 * x.numerator + x.denominator) // (2 * x.denominator)
    return -((-2 * x.numerator + x.denominator) // (2 * x.denominator))


def tax_amount(region, discount_pct, lines) -> int:
    """Return the sales tax for an order in integer cents.

    See the module docstring for the parameter meanings.
    """
    if region is None or str(region).strip() == "":
        return 0

    discount = _to_fraction(discount_pct)
    if discount < 0 or discount > 100:
        raise ValueError(
            f"discount_pct must be between 0 and 100, got {discount_pct!r}"
        )

    rate = _to_fraction(tax_rate(region))  # 0 for unknown regions

    taxable = 0
    for category, line_amount_cents in lines:
        if not is_exempt(category):
            taxable += int(line_amount_cents)

    base = Fraction(taxable) * (100 - discount) / 100
    tax = base * rate / 100
    return _round_half_up(tax)
