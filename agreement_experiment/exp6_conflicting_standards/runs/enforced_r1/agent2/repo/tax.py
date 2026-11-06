"""Tax module. Owned by agent2. Computes sales tax.

The data files and rules are in data_tax/ next to this file.

Interface (committed decision ``tax.interface`` v2):

    sales_tax(lines, region, discount_pct) -> int
        lines        : list of dicts {"category": str, "amount_cents": int}
                       amount_cents is the pre-discount line total, integer cents, >= 0.
        region       : customer region code such as "TX", "NY", "OR", or None
                       for an unknown customer (tax 0, no error).
                       A non-None region not in rates.csv raises KeyError.
        discount_pct : customer discount as a percent number (10 means 10%). 0 if none.
        returns      : tax in integer cents, rounded half up. Never a float.

    tax_rate(region) -> float
        Tax percent for a region. None returns 0.0. Unknown region raises KeyError.

Money is integer cents and percentages are percent numbers. Floats are not
accepted for money; the caller (invoice.py) converts pricing values once at its
boundary.

Formula (from data_tax/RULES.md):
    taxable = sum of amount_cents of taxable lines
    base    = taxable * (100 - discount_pct) / 100        (exact, not rounded)
    tax     = base * rate_pct / 100, rounded half up to the cent
"""

import csv
import os
from decimal import Decimal
from fractions import Fraction
from math import floor

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_tax")
_RATES_PATH = os.path.join(_DATA_DIR, "rates.csv")
_EXEMPT_PATH = os.path.join(_DATA_DIR, "exempt_categories.csv")


def _load_rates(path):
    """Return {region: Fraction percent} from rates.csv. Exact (Decimal string, no float)."""
    rates = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            region = row["region"].strip()
            rates[region] = Fraction(Decimal(row["tax_pct"].strip()))
    return rates


def _load_exempt(path):
    """Return the set of exempt category names from exempt_categories.csv."""
    exempt = set()
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            exempt.add(row["category"].strip())
    return exempt


_RATES = _load_rates(_RATES_PATH)          # {region: Fraction percent}
_EXEMPT = _load_exempt(_EXEMPT_PATH)       # {category, ...}


def tax_rate(region):
    """Tax percent for region (e.g. "TX" -> 8.25). None (unknown customer) -> 0.0.

    Raises KeyError if region is a string that is not in rates.csv.
    """
    if region is None:
        return 0.0
    if region not in _RATES:
        raise KeyError(f"unknown tax region: {region!r}")
    return float(_RATES[region])


def _to_fraction(value, name):
    """Convert a numeric percent/value to an exact Fraction without going through binary float."""
    if isinstance(value, bool) or not isinstance(value, (int, float, Decimal, str)):
        raise TypeError(f"{name} must be a number, got {type(value).__name__}")
    return Fraction(Decimal(str(value)))


def sales_tax(lines, region, discount_pct):
    """Return the sales tax for an order in integer cents, rounded half up.

    See the module docstring for the committed interface.
    """
    taxable = 0
    for line in lines:
        amount = line["amount_cents"]
        category = line["category"]
        if isinstance(amount, bool) or not isinstance(amount, int):
            raise TypeError(f"amount_cents must be an int, got {type(amount).__name__}")
        if amount < 0:
            raise ValueError(f"amount_cents must be >= 0, got {amount}")
        if category not in _EXEMPT:
            taxable += amount

    discount = _to_fraction(discount_pct, "discount_pct")
    if discount < 0 or discount > 100:
        raise ValueError(f"discount_pct must be between 0 and 100, got {discount_pct}")

    if region is None:
        return 0

    if region not in _RATES:
        raise KeyError(f"unknown tax region: {region!r}")
    rate = _RATES[region]

    # base = taxable * (100 - discount) / 100 ; tax = base * rate / 100
    exact_tax = Fraction(taxable) * (100 - discount) * rate / 10000
    # Round half up for non-negative values: floor(x + 1/2).
    return floor(exact_tax + Fraction(1, 2))
