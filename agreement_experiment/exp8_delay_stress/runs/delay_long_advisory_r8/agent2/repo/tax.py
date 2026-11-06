"""Tax module. Owned by agent2. Computes sales tax.

The data files and rules are in data_tax/ next to this file.

Committed API (TAX_API v2, VALUE_CONVENTIONS v2):
    calculate_tax(region: str, discount: Decimal, lines: list[tuple[str, Decimal]]) -> Decimal
        lines    : (category, line_amount_dollars) for every item on the order
        discount : fraction, Decimal("0.10") = 10 percent off
        returns  : tax in dollars, quantized to cents, ROUND_HALF_UP
    tax_rate(region: str) -> Decimal
        fraction, e.g. Decimal("0.0825") for 8.25 percent

Conventions:
    * Money and rates are decimal.Decimal. Floats are rejected with TypeError.
    * A region that is not in rates.csv has rate Decimal("0") (RULES.md: 0% tax).
    * Tax rules (RULES.md):
        taxable = sum of line amounts whose category is NOT exempt
        base    = taxable * (1 - discount)
        tax     = round_half_up(base * rate, cents)
      Rounding is applied once, at the end.
"""

import csv
import os
from decimal import Decimal, ROUND_HALF_UP

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_tax")
_CENT = Decimal("0.01")
_ZERO = Decimal("0")
_ONE = Decimal("1")
_HUNDRED = Decimal("100")


def _load_rates(path):
    rates = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            region = row["region"].strip().upper()
            # rates.csv stores percent numbers (8.25); convert to a fraction.
            rates[region] = Decimal(row["tax_pct"].strip()) / _HUNDRED
    return rates


def _load_exempt(path):
    with open(path, newline="", encoding="utf-8") as f:
        return frozenset(row["category"].strip() for row in csv.DictReader(f))


_RATES = _load_rates(os.path.join(_DATA_DIR, "rates.csv"))
_EXEMPT = _load_exempt(os.path.join(_DATA_DIR, "exempt_categories.csv"))


def tax_rate(region):
    """Return the sales tax rate for a region as a fraction. Unknown region -> Decimal("0")."""
    return _RATES.get(region.strip().upper(), _ZERO)


def _check_decimal(name, value):
    if not isinstance(value, Decimal):
        raise TypeError(f"{name} must be decimal.Decimal, got {type(value).__name__}")


def calculate_tax(region, discount, lines):
    """Return the sales tax in dollars (Decimal, quantized to cents, ROUND_HALF_UP).

    region   : customer region code, e.g. "TX"
    discount : fraction off the taxable amount, e.g. Decimal("0.10") for 10 percent
    lines    : iterable of (category, line_amount) where line_amount is a Decimal in dollars
    """
    _check_decimal("discount", discount)
    if not (_ZERO <= discount <= _ONE):
        raise ValueError(f"discount must be between 0 and 1, got {discount}")

    taxable = _ZERO
    for category, amount in lines:
        _check_decimal("line amount", amount)
        if category.strip() in _EXEMPT:
            continue
        taxable += amount

    base = taxable * (_ONE - discount)
    tax = base * tax_rate(region)
    return tax.quantize(_CENT, rounding=ROUND_HALF_UP)
