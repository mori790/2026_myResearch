"""Tax module. Owned by agent2. Computes sales tax.

The data files and rules are in data_tax/ next to this file (see data_tax/RULES.md).

Public API (money in integer cents, percentages as percent numbers, e.g. 8.25 means 8.25%):

    compute_tax(lines, region, discount_pct=0) -> int
        lines        : iterable of (category: str, amount_cents: int)
        region       : customer's region code (e.g. "TX"), or None for an unknown customer
        discount_pct : customer's discount percent (e.g. 10 for 10%)
        returns      : tax in integer cents, rounded half up to the cent

    tax_pct(region) -> float
        Tax percent for a region. None (unknown customer) -> 0.0.
        Raises KeyError if the region is not in rates.csv.

    is_exempt(category) -> bool
        True if items of this category are not taxed (exempt_categories.csv).
"""

import csv
import os
from decimal import ROUND_HALF_UP, Decimal

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_tax")
_RATES_PATH = os.path.join(_DATA_DIR, "rates.csv")
_EXEMPT_PATH = os.path.join(_DATA_DIR, "exempt_categories.csv")

_HUNDRED = Decimal(100)
_CENT = Decimal(1)


def _load_rates(path):
    with open(path, newline="", encoding="utf-8") as f:
        return {
            row["region"].strip(): Decimal(row["tax_pct"].strip())
            for row in csv.DictReader(f)
        }


def _load_exempt(path):
    with open(path, newline="", encoding="utf-8") as f:
        return frozenset(
            row["category"].strip() for row in csv.DictReader(f) if row["category"].strip()
        )


_RATES = _load_rates(_RATES_PATH)
_EXEMPT_CATEGORIES = _load_exempt(_EXEMPT_PATH)


def is_exempt(category):
    """Return True if items in `category` are not taxed."""
    return category in _EXEMPT_CATEGORIES


def tax_pct(region):
    """Return the tax percent for `region`. None (unknown customer) gives 0.

    Raises KeyError if `region` is a string that is not in rates.csv.
    """
    if region is None:
        return 0.0
    return float(_RATES[region])


def compute_tax(lines, region, discount_pct=0):
    """Compute the sales tax for one order, in integer cents.

    Rules (data_tax/RULES.md):
      - taxable_sum = sum of line amounts whose category is not exempt
      - base        = taxable_sum * (100 - discount_pct) / 100
      - tax         = base * tax_pct / 100, rounded half up to the cent
      - unknown customer (region None) pays 0 tax
    """
    if region is None:
        return 0

    # Look up the rate first so an unknown region raises KeyError even
    # when no line is taxable.
    rate = _RATES[region]

    taxable_sum = Decimal(0)
    for category, amount_cents in lines:
        if not is_exempt(category):
            taxable_sum += Decimal(str(amount_cents))

    discount = Decimal(str(discount_pct))
    if discount < 0 or discount > 100:
        raise ValueError(f"discount_pct must be between 0 and 100, got {discount_pct!r}")

    base = taxable_sum * (_HUNDRED - discount) / _HUNDRED
    tax = base * rate / _HUNDRED
    return int(tax.quantize(_CENT, rounding=ROUND_HALF_UP))
