"""Tax module. Owned by agent2. Computes sales tax.

The data files and rules are in data_tax/ next to this file.

Public API (all money in integer cents, all percentages as percent numbers):

    tax_pct_for_region(region) -> Decimal
        Tax percent for a customer region. region=None means an unknown
        customer and gives 0. A region that is not in rates.csv raises KeyError.

    is_exempt(category) -> bool
        True if the item category is listed in exempt_categories.csv.

    compute_tax(lines, discount_pct, region) -> int
        lines: iterable of (category, amount_cents) pairs for the order lines.
        discount_pct: the customer's discount, e.g. 10 for 10%.
        region: the customer's region code, or None for an unknown customer.
        Returns the tax in integer cents, rounded half up.

Rule (data_tax/RULES.md):
    taxable_amount = sum of amounts of lines whose category is not exempt
    base           = taxable_amount * (100 - discount_pct) / 100
    tax            = base * tax_pct / 100, rounded to the cent (half up)
"""

import csv
import os
from decimal import Decimal, ROUND_HALF_UP

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_tax")
_RATES_PATH = os.path.join(_DATA_DIR, "rates.csv")
_EXEMPT_PATH = os.path.join(_DATA_DIR, "exempt_categories.csv")


def _load_rates():
    rates = {}
    with open(_RATES_PATH, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            rates[row["region"].strip()] = Decimal(row["tax_pct"].strip())
    return rates


def _load_exempt():
    exempt = set()
    with open(_EXEMPT_PATH, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            category = (row.get("category") or "").strip()
            if category:
                exempt.add(category)
    return frozenset(exempt)


_RATES = _load_rates()
_EXEMPT = _load_exempt()


def _to_decimal(value, name):
    if isinstance(value, bool):
        raise TypeError(f"{name} must be a number, not bool")
    if isinstance(value, Decimal):
        return value
    if isinstance(value, (int, float, str)):
        return Decimal(str(value))
    raise TypeError(f"{name} must be a number, got {type(value).__name__}")


def tax_pct_for_region(region):
    """Return the tax percent for a region. None (unknown customer) gives 0.

    Raises KeyError if the region is not listed in rates.csv.
    """
    if region is None:
        return Decimal(0)
    return _RATES[region]


def is_exempt(category):
    """True if items of this category are not taxed."""
    return category in _EXEMPT


def compute_tax(lines, discount_pct, region):
    """Compute the sales tax for an order, in integer cents.

    lines: iterable of (category, amount_cents) pairs.
    discount_pct: customer discount in percent (0-100).
    region: customer region code, or None for an unknown customer.
    """
    taxable = 0
    for category, amount_cents in lines:
        if isinstance(amount_cents, bool) or not isinstance(amount_cents, int):
            raise TypeError("amount_cents must be an integer number of cents")
        if amount_cents < 0:
            raise ValueError("amount_cents must not be negative")
        if not is_exempt(category):
            taxable += amount_cents

    discount = _to_decimal(discount_pct, "discount_pct")
    if discount < 0 or discount > 100:
        raise ValueError("discount_pct must be between 0 and 100")

    tax_pct = tax_pct_for_region(region)

    base = Decimal(taxable) * (Decimal(100) - discount) / Decimal(100)
    tax = base * tax_pct / Decimal(100)
    return int(tax.quantize(Decimal(1), rounding=ROUND_HALF_UP))
