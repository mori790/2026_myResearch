"""Tax module. Owned by agent2. Computes sales tax.

The data files and rules are in data_tax/ next to this file.

Public API (all money in integer cents, all percentages as percent numbers):

    tax_pct(region) -> Decimal
        Tax percent for a region, e.g. Decimal("8.25") for "TX".
        region=None means "unknown customer" and gives Decimal("0").
        Raises KeyError for a region that is not in rates.csv.

    is_exempt(category) -> bool
        True if the item category is listed in exempt_categories.csv.

    compute_tax(region, lines, discount_pct=0) -> int
        region:       customer region (str), or None for an unknown customer.
        lines:        iterable of (category, amount_cents) pairs, one per line item.
        discount_pct: customer discount in percent (e.g. 10 for 10%).
        Returns the tax in integer cents, rounded half up to the cent.

Rules (data_tax/RULES.md):
    taxable  = sum of amount_cents over lines whose category is not exempt
    base     = taxable * (100 - discount_pct) / 100
    tax      = base * tax_pct / 100, rounded to the cent (half up)
"""

import csv
import os
from decimal import Decimal, ROUND_HALF_UP

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_tax")


def _norm_region(region):
    return str(region).strip().upper()


def _norm_category(category):
    return str(category).strip().lower()


def _load_rates():
    rates = {}
    path = os.path.join(_DATA_DIR, "rates.csv")
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            region = _norm_region(row["region"])
            if region:
                rates[region] = Decimal(row["tax_pct"].strip())
    return rates


def _load_exempt_categories():
    exempt = set()
    path = os.path.join(_DATA_DIR, "exempt_categories.csv")
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            category = _norm_category(row["category"])
            if category:
                exempt.add(category)
    return exempt


_RATES = _load_rates()
_EXEMPT_CATEGORIES = _load_exempt_categories()


def _to_decimal(value, name):
    if isinstance(value, bool):
        raise TypeError(f"{name} must be a number, not bool")
    if isinstance(value, (int, Decimal)):
        return Decimal(value)
    if isinstance(value, float):
        # Go through str() so 8.25 becomes exactly Decimal("8.25").
        return Decimal(str(value))
    if isinstance(value, str):
        return Decimal(value.strip())
    raise TypeError(f"{name} must be a number, got {type(value).__name__}")


def tax_pct(region):
    """Return the tax percent for a region as a Decimal.

    None (unknown customer) -> Decimal("0").
    A region not in rates.csv -> KeyError.
    """
    if region is None:
        return Decimal("0")
    return _RATES[_norm_region(region)]


def is_exempt(category):
    """True if items of this category are not taxed."""
    return _norm_category(category) in _EXEMPT_CATEGORIES


def compute_tax(region, lines, discount_pct=0):
    """Return the sales tax for an order, in integer cents.

    region:       customer region, or None for an unknown customer (tax 0).
    lines:        iterable of (category, amount_cents) pairs.
    discount_pct: customer discount in percent.
    """
    discount = _to_decimal(discount_pct, "discount_pct")
    if not (Decimal(0) <= discount <= Decimal(100)):
        raise ValueError(f"discount_pct must be between 0 and 100, got {discount_pct}")

    taxable = 0
    for category, amount_cents in lines:
        if isinstance(amount_cents, bool) or not isinstance(amount_cents, int):
            raise TypeError(f"amount_cents must be an int (cents), got {amount_cents!r}")
        if not is_exempt(category):
            taxable += amount_cents

    pct = tax_pct(region)  # KeyError for an unknown, non-None region.
    if pct == 0 or taxable == 0:
        return 0

    # base = taxable * (100 - discount) / 100; tax = base * pct / 100 (in cents).
    # Computed exactly with Decimal and rounded once, half up, at the end.
    exact_tax = Decimal(taxable) * (Decimal(100) - discount) * pct / Decimal(10000)
    return int(exact_tax.quantize(Decimal(1), rounding=ROUND_HALF_UP))
