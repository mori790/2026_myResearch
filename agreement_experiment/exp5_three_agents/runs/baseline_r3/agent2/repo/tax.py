"""Tax module. Owned by agent2. Computes sales tax.

The data files and rules are in data_tax/ next to this file (see data_tax/RULES.md).

Public API (all money values are decimal.Decimal, rounded to the cent):

    tax_rate(region) -> Decimal
        Tax percent for a region code, e.g. Decimal("8.25") for "TX".
        Returns Decimal("0") for an unknown region or for region None
        (unknown customer pays 0% tax).

    is_exempt(category) -> bool
        True if the item category is listed in exempt_categories.csv.

    taxable_base(lines, discount_pct) -> Decimal
        Discounted taxable base: taxable_amount * (100 - discount_pct) / 100.

    compute_tax(region, discount_pct, lines) -> Decimal
        Sales tax for one order: round_half_up(base * tax_pct / 100, cent).

    lines is an iterable of (amount, category) pairs, where amount is the
    line amount (Decimal, int, float or str) and category is the item's
    category string. discount_pct is the customer's discount in percent
    (0-100); None is treated as 0.
"""

import csv
import os
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_tax")
_RATES_PATH = os.path.join(_DATA_DIR, "rates.csv")
_EXEMPT_PATH = os.path.join(_DATA_DIR, "exempt_categories.csv")

_CENT = Decimal("0.01")
_HUNDRED = Decimal("100")
_ZERO = Decimal("0")


def _to_decimal(value, name):
    if isinstance(value, Decimal):
        return value
    try:
        # Go through str so that floats like 0.1 become Decimal("0.1").
        return Decimal(str(value).strip())
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ValueError(f"{name} is not a valid number: {value!r}") from exc


def _normalize_key(text):
    return str(text).strip().upper()


def _load_rates(path=_RATES_PATH):
    rates = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            region = _normalize_key(row["region"])
            if region:
                rates[region] = _to_decimal(row["tax_pct"], "tax_pct")
    return rates


def _load_exempt_categories(path=_EXEMPT_PATH):
    exempt = set()
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            category = str(row.get("category", "")).strip().lower()
            if category:
                exempt.add(category)
    return frozenset(exempt)


_RATES = _load_rates()
_EXEMPT_CATEGORIES = _load_exempt_categories()


def tax_rate(region):
    """Return the tax percent for a region (Decimal). Unknown region -> 0."""
    if region is None:
        return _ZERO
    return _RATES.get(_normalize_key(region), _ZERO)


def is_exempt(category):
    """True if items of this category are not taxed."""
    if category is None:
        return False
    return str(category).strip().lower() in _EXEMPT_CATEGORIES


def taxable_base(lines, discount_pct):
    """Sum of taxable line amounts, reduced by the customer's discount percent.

    base = taxable_amount * (100 - discount_pct) / 100
    Rounding is NOT applied here; it is applied once in compute_tax.
    """
    taxable_amount = _ZERO
    for amount, category in lines:
        if not is_exempt(category):
            taxable_amount += _to_decimal(amount, "amount")

    discount = _ZERO if discount_pct is None else _to_decimal(discount_pct, "discount_pct")
    if discount < _ZERO or discount > _HUNDRED:
        raise ValueError(f"discount_pct must be between 0 and 100, got {discount}")

    return taxable_amount * (_HUNDRED - discount) / _HUNDRED


def compute_tax(region, discount_pct, lines):
    """Sales tax for one order, rounded to the cent (half up).

    tax = base * tax_pct / 100, where base = taxable_base(lines, discount_pct)
    and tax_pct = tax_rate(region).
    """
    base = taxable_base(lines, discount_pct)
    rate = tax_rate(region)
    tax = base * rate / _HUNDRED
    return tax.quantize(_CENT, rounding=ROUND_HALF_UP)
