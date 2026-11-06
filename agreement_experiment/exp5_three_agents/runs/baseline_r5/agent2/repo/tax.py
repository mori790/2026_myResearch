"""Tax module. Owned by agent2. Computes sales tax.

The data files and rules are in data_tax/ next to this file:
  - data_tax/rates.csv              region -> tax_pct
  - data_tax/exempt_categories.csv  item categories that are not taxed
  - data_tax/RULES.md               the rules implemented here

Public API
----------
compute_tax(lines, region, discount_pct=0) -> Decimal
    lines         iterable of line items. Each item is either a mapping with
                  keys "category" and "amount", or a 2-tuple (category, amount).
                  "amount" is the line total (int, str, Decimal or float).
    region        customer's region code (e.g. "TX"), or None for an unknown
                  customer. Unknown regions pay 0%.
    discount_pct  customer's discount percent (e.g. 10 for 10%). Default 0.
    Returns the tax amount as a Decimal rounded to the cent (ROUND_HALF_UP).

tax_breakdown(lines, region, discount_pct=0) -> dict
    Same inputs; returns a dict with the intermediate values:
    taxable_amount, discount_pct, base, tax_pct, tax.

Rules (from RULES.md)
---------------------
  taxable_amount = sum of line amounts whose category is NOT exempt
  base           = taxable_amount * (100 - discount_pct) / 100
  tax            = base * tax_pct / 100, rounded to the cent (half up)
The rounding is applied once, to the final tax, not per line.
"""

import csv
import os
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from typing import Iterable, Mapping, Optional, Tuple, Union

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_tax")
_RATES_PATH = os.path.join(_DATA_DIR, "rates.csv")
_EXEMPT_PATH = os.path.join(_DATA_DIR, "exempt_categories.csv")

_CENT = Decimal("0.01")
_ZERO = Decimal("0")
_HUNDRED = Decimal("100")


def _norm_key(value) -> str:
    return str(value).strip().upper()


def _norm_category(value) -> str:
    return str(value).strip().lower()


def _to_decimal(value, name: str) -> Decimal:
    if isinstance(value, bool):
        raise TypeError(f"{name} must be a number, not bool")
    if isinstance(value, Decimal):
        return value
    if isinstance(value, float):
        # Go through str() to avoid binary float artifacts (0.1 -> 0.1000000000000000055...).
        value = str(value)
    try:
        return Decimal(str(value).strip())
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"{name} is not a valid number: {value!r}") from exc


def _load_rates(path: str = _RATES_PATH) -> dict:
    rates = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            region = _norm_key(row["region"])
            if region:
                rates[region] = _to_decimal(row["tax_pct"], "tax_pct")
    return rates


def _load_exempt_categories(path: str = _EXEMPT_PATH) -> frozenset:
    exempt = set()
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            category = _norm_category(row["category"])
            if category:
                exempt.add(category)
    return frozenset(exempt)


_RATES = _load_rates()
_EXEMPT = _load_exempt_categories()


def tax_rate_for_region(region: Optional[str]) -> Decimal:
    """Return the tax percent for a region. Unknown or missing region -> 0."""
    if region is None:
        return _ZERO
    return _RATES.get(_norm_key(region), _ZERO)


def is_exempt(category) -> bool:
    """True if items in this category are not taxed."""
    return _norm_category(category) in _EXEMPT


def _line_category_and_amount(line) -> Tuple[str, Decimal]:
    if isinstance(line, Mapping):
        category = line["category"]
        amount = line["amount"]
    else:
        category, amount = line
    return category, _to_decimal(amount, "amount")


def tax_breakdown(
    lines: Iterable[Union[Mapping, Tuple]],
    region: Optional[str],
    discount_pct=0,
) -> dict:
    """Compute tax and return the intermediate values as a dict."""
    taxable_amount = _ZERO
    for line in lines:
        category, amount = _line_category_and_amount(line)
        if not is_exempt(category):
            taxable_amount += amount

    discount = _to_decimal(discount_pct, "discount_pct")
    tax_pct = tax_rate_for_region(region)

    base = taxable_amount * (_HUNDRED - discount) / _HUNDRED
    tax = (base * tax_pct / _HUNDRED).quantize(_CENT, rounding=ROUND_HALF_UP)

    return {
        "taxable_amount": taxable_amount,
        "discount_pct": discount,
        "base": base,
        "tax_pct": tax_pct,
        "tax": tax,
    }


def compute_tax(
    lines: Iterable[Union[Mapping, Tuple]],
    region: Optional[str],
    discount_pct=0,
) -> Decimal:
    """Return the sales tax for an order, rounded to the cent (half up)."""
    return tax_breakdown(lines, region, discount_pct)["tax"]
