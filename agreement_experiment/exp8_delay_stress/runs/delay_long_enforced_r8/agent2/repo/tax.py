"""Tax module. Owned by agent2. Computes sales tax.

The data files and rules are in data_tax/ next to this file (see data_tax/RULES.md).

Committed interface (decision topic ``tax_api``):

    compute_tax_cents(region, lines, discount_pct=0) -> int

* ``region``: customer region code as in data_tax/rates.csv (e.g. "TX").
  ``None`` means an unknown customer, who pays 0 tax.
  A non-None region that is not in rates.csv raises KeyError.
* ``lines``: list of dicts ``{"category": str, "amount_cents": int}``.
  ``amount_cents`` is the line total in integer cents (quantity already included).
  Lines whose category is listed in exempt_categories.csv are not taxed.
* ``discount_pct``: percent number (10 means 10%).
* Returns an ``int`` tax amount in cents.

Arithmetic:

    taxable_sum = sum of amount_cents over non-exempt lines
    base        = taxable_sum * (100 - discount_pct) / 100
    tax         = base * rate_pct / 100, rounded once to the cent (half up)

Exact rational arithmetic (``fractions.Fraction``) is used, so no float error enters.
"""

import csv
import os
from decimal import Decimal
from fractions import Fraction

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_tax")


def _load_rates(path):
    rates = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            region = (row.get("region") or "").strip()
            pct = (row.get("tax_pct") or "").strip()
            if region and pct:
                rates[region] = Decimal(pct)
    return rates


def _load_exempt(path):
    exempt = set()
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            category = (row.get("category") or "").strip().lower()
            if category:
                exempt.add(category)
    return exempt


_RATES = _load_rates(os.path.join(_DATA_DIR, "rates.csv"))            # region -> Decimal percent
_EXEMPT = _load_exempt(os.path.join(_DATA_DIR, "exempt_categories.csv"))  # lower-case categories


def tax_rate_pct(region):
    """Return the tax percent for a region (e.g. Decimal('8.25') for TX).

    ``None`` (unknown customer) gives Decimal('0').
    A region not listed in rates.csv raises KeyError.
    """
    if region is None:
        return Decimal("0")
    return _RATES[region]


def is_exempt(category):
    """Return True if items in this category are not taxed."""
    return str(category).strip().lower() in _EXEMPT


def _to_fraction(value, name):
    if isinstance(value, bool):
        raise TypeError(f"{name} must be a number, not bool")
    if isinstance(value, int):
        return Fraction(value)
    if isinstance(value, (float, Decimal, str)):
        # Use the textual form so 8.25 becomes exactly 8.25, not a binary float.
        return Fraction(str(value))
    raise TypeError(f"{name} must be a number, got {type(value).__name__}")


def _round_half_up(x):
    """Round a non-negative Fraction to the nearest integer, halves going up."""
    return int(x + Fraction(1, 2)) if x >= 0 else -int(-x + Fraction(1, 2))


def compute_tax_cents(region, lines, discount_pct=0):
    """Compute the sales tax for an order, in integer cents.

    See the module docstring for the rules and the arguments.
    """
    rate = _to_fraction(tax_rate_pct(region), "tax rate")

    discount = _to_fraction(discount_pct, "discount_pct")
    if discount < 0 or discount > 100:
        raise ValueError(f"discount_pct must be between 0 and 100, got {discount_pct}")

    taxable_sum = 0
    for line in lines:
        amount = line["amount_cents"]
        if isinstance(amount, bool) or not isinstance(amount, int):
            raise TypeError(f"amount_cents must be an int, got {amount!r}")
        if is_exempt(line["category"]):
            continue
        taxable_sum += amount

    base = Fraction(taxable_sum) * (100 - discount) / 100
    tax = base * rate / 100
    return _round_half_up(tax)
