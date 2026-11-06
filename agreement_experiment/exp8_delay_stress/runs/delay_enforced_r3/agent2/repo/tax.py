"""Sales tax module (owned by agent2).

Implements the committed team decisions:

* TAX_API v1: ``compute_tax(lines, region, discount_pct) -> int`` (tax in cents).
  - Money is integer cents; percentages are percent numbers (10 means 10%).
  - ``lines`` is a list of ``{"category": str, "amount_cents": int}``.
  - ``region`` is the customer's region code (e.g. ``"TX"``) or ``None`` for an
    unknown customer.
  - Tax base  = taxable_cents * (100 - discount_pct) / 100   (exact, no rounding)
  - Tax       = base * tax_pct / 100, rounded once to the cent, half up.
  - ``tax_pct(region)`` raises ``KeyError`` for a region not in rates.csv.
* UNKNOWN_CUSTOMER_TAX v1: ``region=None`` means unknown customer -> tax 0.
* EXEMPT_SIGNAL v1: a line is taxable unless its category is listed in
  exempt_categories.csv. This module decides exemption, not the caller.

Data files are loaded relative to this module file (``data_tax/``).
"""

import csv
import os
from fractions import Fraction

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_tax")
_RATES_PATH = os.path.join(_DATA_DIR, "rates.csv")
_EXEMPT_PATH = os.path.join(_DATA_DIR, "exempt_categories.csv")


def _load_rates(path=_RATES_PATH):
    """Return {region: Fraction(tax percent)} parsed exactly from the CSV text."""
    rates = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            region = row["region"].strip()
            rates[region] = Fraction(row["tax_pct"].strip())
    return rates


def _load_exempt_categories(path=_EXEMPT_PATH):
    """Return the set of exempt category names (normalized to lower case)."""
    exempt = set()
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            name = row["category"].strip().lower()
            if name:
                exempt.add(name)
    return exempt


_RATES = _load_rates()
_EXEMPT = _load_exempt_categories()


def tax_pct(region):
    """Return the tax percent for ``region`` as a float (e.g. 8.25).

    Raises KeyError if the region is not listed in rates.csv.
    """
    if region not in _RATES:
        raise KeyError(f"no tax rate for region {region!r}")
    return float(_RATES[region])


def is_exempt(category):
    """Return True if items in ``category`` are not taxed."""
    return str(category).strip().lower() in _EXEMPT


def _round_half_up(value):
    """Round a non-negative Fraction to the nearest integer, ties upward."""
    return (value + Fraction(1, 2)).__floor__()


def compute_tax(lines, region, discount_pct):
    """Return the sales tax in integer cents.

    lines        -- iterable of dicts with keys ``category`` (str) and
                    ``amount_cents`` (int, line total before tax and discount).
    region       -- customer region code, or None for an unknown customer.
    discount_pct -- customer discount as a percent number in 0..100.
    """
    if region is None:
        # UNKNOWN_CUSTOMER_TAX: an unknown customer pays no tax.
        return 0

    if isinstance(discount_pct, bool) or not isinstance(discount_pct, (int, float, Fraction)):
        raise TypeError("discount_pct must be a number (percent, 0..100)")
    if not 0 <= discount_pct <= 100:
        raise ValueError(f"discount_pct must be in 0..100, got {discount_pct!r}")

    taxable_cents = 0
    for line in lines:
        amount = line["amount_cents"]
        if isinstance(amount, bool) or not isinstance(amount, int):
            raise TypeError("amount_cents must be an int (cents)")
        if amount < 0:
            raise ValueError("amount_cents must be non-negative")
        if not is_exempt(line["category"]):
            taxable_cents += amount

    # Look up the rate even when nothing is taxable, so an unknown region
    # raises KeyError consistently (team standard).
    if region not in _RATES:
        raise KeyError(f"no tax rate for region {region!r}")
    rate = _RATES[region]

    if taxable_cents == 0:
        return 0

    # Exact arithmetic: no intermediate rounding of the base.
    base = Fraction(taxable_cents) * (100 - Fraction(discount_pct)) / 100
    tax_exact = base * rate / 100
    return _round_half_up(tax_exact)
