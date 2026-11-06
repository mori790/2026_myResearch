"""Tax module. Owned by agent2. Computes sales tax. The data files and rules are in data_tax/ next to this file.

Committed API (agree.py: tax_api v1, money_units v1, unknown_customer v2):
    compute_tax(region, lines, discount_pct) -> int
        Tax in integer cents. region is a region code (e.g. "TX"), or None for an
        unknown customer (tax 0). lines is an iterable of (category, amount_cents).
        discount_pct is the customer's discount as a percent number (10 = 10%).
    tax_rate(region) -> float
        Tax percent number for a region (8.25 = 8.25%), or 0 for None.

Rules (data_tax/RULES.md):
    taxable  = sum of line amounts whose category is NOT in exempt_categories.csv
    base     = taxable * (100 - discount_pct) / 100
    tax      = base * tax_pct / 100, rounded to the cent (half up, away from zero)
Arithmetic is exact (fractions.Fraction), so no floating-point error.
"""

import csv
import math
import os
from fractions import Fraction

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_tax")
_HUNDRED = Fraction(100)


def _load_rates():
    """Return {region: Fraction(tax_pct)} from rates.csv."""
    rates = {}
    with open(os.path.join(_DATA_DIR, "rates.csv"), newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            region = (row.get("region") or "").strip()
            pct = (row.get("tax_pct") or "").strip()
            if region and pct:
                rates[region] = Fraction(pct)
    return rates


def _load_exempt():
    """Return the set of tax-exempt categories from exempt_categories.csv."""
    exempt = set()
    with open(os.path.join(_DATA_DIR, "exempt_categories.csv"), newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            category = (row.get("category") or "").strip()
            if category:
                exempt.add(category)
    return exempt


_RATES = _load_rates()
_EXEMPT = _load_exempt()


def _rate_for(region):
    """Exact tax percent (Fraction) for a region. Unknown region -> KeyError."""
    if not isinstance(region, str) or region not in _RATES:
        raise KeyError(region)
    return _RATES[region]


def _to_exact_number(value, name):
    """Convert an int or finite float to an exact Fraction. Other types -> ValueError."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a number, got {value!r}")
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError(f"{name} must be finite, got {value!r}")
        return Fraction(repr(value))  # exact decimal reading, e.g. 8.5 -> 17/2
    return Fraction(value)


def _is_cents(value):
    return isinstance(value, int) and not isinstance(value, bool)


def _round_half_up(value):
    """Round a non-negative Fraction to the nearest integer, halves going up."""
    sign = -1 if value < 0 else 1
    return sign * int(abs(value) + Fraction(1, 2))


def compute_tax(region, lines, discount_pct):
    """Return the sales tax for an order, in integer cents.

    region       : region code such as "TX", or None for an unknown customer (tax 0).
    lines        : iterable of (category, amount_cents) pairs, one per invoice line.
    discount_pct : customer discount as a percent number (0 if none).

    Raises KeyError if region is a string not listed in rates.csv.
    Raises ValueError for non-integer or negative amounts, or a discount outside 0..100.
    """
    discount = _to_exact_number(discount_pct, "discount_pct")
    if not 0 <= discount <= 100:
        raise ValueError(f"discount_pct must be between 0 and 100, got {discount_pct!r}")

    taxable = 0
    for category, amount_cents in lines:
        if not _is_cents(amount_cents) or amount_cents < 0:
            raise ValueError(f"amount_cents must be a non-negative integer, got {amount_cents!r}")
        if category not in _EXEMPT:
            taxable += amount_cents

    if region is None:  # unknown customer pays no tax (RULES.md)
        return 0

    rate = _rate_for(region)
    base = Fraction(taxable) * (_HUNDRED - discount) / _HUNDRED
    tax = base * rate / _HUNDRED
    return _round_half_up(tax)


def tax_rate(region):
    """Return the tax percent number for a region (e.g. 8.25), or 0 for None.

    Raises KeyError if region is a string not listed in rates.csv.
    """
    if region is None:
        return 0
    return float(_rate_for(region))
