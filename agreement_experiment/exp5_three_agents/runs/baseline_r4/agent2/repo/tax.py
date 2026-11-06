"""Tax module. Owned by agent2. Computes sales tax.

The data files and rules are in data_tax/ next to this file (see data_tax/RULES.md).

Public API
----------
compute_tax(lines, region, discount_pct=0) -> Decimal
    Total sales tax for one order.
    lines        : iterable of line items. Each item is either a mapping with keys
                   "amount" and "category", or an object with attributes
                   ``amount`` and ``category``. ``amount`` is the line amount
                   (money, as Decimal/int/float/str); ``category`` is the item
                   category string (e.g. "food").
    region       : customer's region code (e.g. "TX", "NY", "OR"), or None when
                   the customer is unknown (unknown customer pays 0% tax).
    discount_pct : customer's discount percent, 0..100 (default 0).

tax_pct_for_region(region) -> Decimal
    Tax percent for a region (None -> 0).

is_exempt(category) -> bool
    True if the category is listed in exempt_categories.csv (not taxed).

Rules implemented (RULES.md):
    taxable_amount = sum of amounts of non-exempt lines
    base           = taxable_amount * (100 - discount_pct) / 100
    tax            = base * tax_pct / 100, rounded to the cent, half up
    unknown customer (region None) -> 0% tax
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
    """Convert a number-like value to Decimal without going through binary float error."""
    if isinstance(value, Decimal):
        return value
    try:
        return Decimal(str(value).strip())
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ValueError(f"{name} is not a valid number: {value!r}") from exc


def _load_rates(path=_RATES_PATH):
    rates = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            region = row["region"].strip().upper()
            rates[region] = _to_decimal(row["tax_pct"].strip(), "tax_pct")
    return rates


def _load_exempt(path=_EXEMPT_PATH):
    exempt = set()
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            cat = (row.get("category") or "").strip().lower()
            if cat:
                exempt.add(cat)
    return exempt


_RATES = _load_rates()
_EXEMPT = _load_exempt()


def tax_pct_for_region(region):
    """Tax percent for a customer region. Unknown customer (None) pays 0%.

    Raises ValueError for a region code that is not in rates.csv, so that a
    typo or an unsupported region is reported instead of silently taxed at 0%.
    """
    if region is None:
        return _ZERO
    key = str(region).strip().upper()
    if key not in _RATES:
        raise ValueError(f"no tax rate configured for region {region!r}")
    return _RATES[key]


def is_exempt(category):
    """True if items in this category are not taxed."""
    if category is None:
        return False
    return str(category).strip().lower() in _EXEMPT


def _line_field(line, name):
    if isinstance(line, dict) or hasattr(line, "keys"):
        return line[name]
    return getattr(line, name)


def compute_tax(lines, region, discount_pct=0):
    """Return the sales tax for an order as a Decimal rounded to the cent."""
    discount = _to_decimal(discount_pct, "discount_pct")
    if discount < _ZERO or discount > _HUNDRED:
        raise ValueError(f"discount_pct must be between 0 and 100, got {discount_pct!r}")

    taxable = _ZERO
    for line in lines:
        category = _line_field(line, "category")
        if is_exempt(category):
            continue
        taxable += _to_decimal(_line_field(line, "amount"), "amount")

    base = taxable * (_HUNDRED - discount) / _HUNDRED
    tax = base * tax_pct_for_region(region) / _HUNDRED
    return tax.quantize(_CENT, rounding=ROUND_HALF_UP)
