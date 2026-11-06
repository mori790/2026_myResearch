"""Tax module. Owned by agent2. Computes sales tax.

The data files and rules are in data_tax/ next to this file.

Agreed interface (decision log: TAX_API, TAX_UNKNOWN_CUSTOMER):
  compute_tax(lines, region, discount_pct) -> int   (total tax in integer cents)
  tax_pct(region) -> float                          (tax rate as a percent number)

Units: money is integer cents (1250 == $12.50); percents are percent numbers
(8.25 == 8.25%, 10 == 10%).
"""

import csv
import math
from fractions import Fraction
from pathlib import Path

_DATA_DIR = Path(__file__).resolve().parent / "data_tax"


def _load_rates():
    """Return {region_code: tax percent as an exact Fraction} from rates.csv."""
    rates = {}
    with open(_DATA_DIR / "rates.csv", newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            rates[row["region"].strip()] = Fraction(row["tax_pct"].strip())
    return rates


def _load_exempt_categories():
    """Return the set of category names that are not taxed (exempt_categories.csv)."""
    exempt = set()
    with open(_DATA_DIR / "exempt_categories.csv", newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            name = (row.get("category") or "").strip()
            if name:
                exempt.add(name)
    return exempt


_RATES = _load_rates()
_EXEMPT_CATEGORIES = _load_exempt_categories()


def _rate_percent(region):
    """Exact tax percent for a region. None (unknown customer) -> 0.

    Raises KeyError if region is a string that is not in rates.csv.
    """
    if region is None:
        return Fraction(0)
    return _RATES[region]


def tax_pct(region):
    """Tax rate for a region as a percent number (8.25 == 8.25%).

    None (unknown customer) -> 0.0. Unknown region string -> KeyError.
    """
    return float(_rate_percent(region))


def _to_fraction(value, name):
    """Convert an int/float/Fraction to an exact Fraction, rejecting bools and others."""
    if isinstance(value, bool) or not isinstance(value, (int, float, Fraction)):
        raise ValueError(f"{name} must be a number, got {value!r}")
    if isinstance(value, float):
        # Use the decimal repr so 8.25 becomes exactly 825/100, not a binary approximation.
        return Fraction(repr(value))
    return Fraction(value)


def compute_tax(lines, region, discount_pct):
    """Return the total sales tax for an order, in integer cents.

    lines:        iterable of (category: str, amount_cents: int), pre-discount line amounts.
    region:       customer region code as in data_tax/rates.csv, or None for an unknown customer.
    discount_pct: customer discount as a percent number, 0..100 (10 == 10% off).

    Rules (data_tax/RULES.md):
      taxable_amount = sum of line amounts whose category is not exempt
      base           = taxable_amount * (100 - discount_pct) / 100
      tax            = base * tax_pct / 100, rounded to the cent, half up
    The rounding is applied once, to the total, not per line.
    """
    discount = _to_fraction(discount_pct, "discount_pct")
    if not (0 <= discount <= 100):
        raise ValueError(f"discount_pct must be in 0..100, got {discount_pct!r}")

    taxable_cents = 0
    for line in lines:
        category, amount_cents = line
        if not isinstance(category, str):
            raise ValueError(f"line category must be a str, got {category!r}")
        if isinstance(amount_cents, bool) or not isinstance(amount_cents, int):
            raise ValueError(f"line amount_cents must be an int, got {amount_cents!r}")
        if amount_cents < 0:
            raise ValueError(f"line amount_cents must not be negative, got {amount_cents!r}")
        if category not in _EXEMPT_CATEGORIES:
            taxable_cents += amount_cents

    rate = _rate_percent(region)  # KeyError for an unknown region string

    # Exact arithmetic: taxable * (100 - d)/100 * rate/100, all in cents.
    exact_tax_cents = Fraction(taxable_cents) * (100 - discount) / 100 * rate / 100

    # ROUND_HALF_UP; the value is never negative here.
    return math.floor(exact_tax_cents + Fraction(1, 2))
