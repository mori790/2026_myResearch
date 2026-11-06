"""Tax module. Owned by agent2. Computes sales tax.

The data files and rules are in data_tax/ next to this file:
  - data_tax/rates.csv              region,tax_pct
  - data_tax/exempt_categories.csv  category
  - data_tax/RULES.md               the rules this module implements

Public API (all money values are decimal.Decimal, rounded to the cent):

  tax_rate_pct(region) -> Decimal
      Tax percent for a customer region. Unknown or missing region -> Decimal("0").

  is_exempt(category) -> bool
      True if the item category is listed in exempt_categories.csv.

  compute_tax(lines, region, discount_pct=0) -> Decimal
      lines:        iterable of (category, amount) pairs, one per line item.
                    amount is the line amount (price * quantity).
      region:       customer region code, e.g. "TX"; None for an unknown customer.
      discount_pct: customer discount percent in [0, 100].
      Returns the sales tax for the order.

Rule (RULES.md):
  taxable_amount = sum of line amounts whose category is NOT exempt
  base           = taxable_amount * (100 - discount_pct) / 100
  tax            = base * tax_pct / 100, rounded to the cent (half up)
"""

import csv
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from functools import lru_cache
from pathlib import Path

_DATA_DIR = Path(__file__).resolve().parent / "data_tax"
_CENT = Decimal("0.01")
_HUNDRED = Decimal("100")


def _to_decimal(value, name):
    """Convert a number or numeric string to Decimal without float noise."""
    if isinstance(value, bool):
        raise TypeError(f"{name} must be a number, not bool")
    if isinstance(value, Decimal):
        result = value
    elif isinstance(value, float):
        result = Decimal(str(value))
    else:
        try:
            result = Decimal(str(value).strip())
        except (InvalidOperation, ValueError):
            raise ValueError(f"{name} is not a valid number: {value!r}") from None
    if not result.is_finite():
        raise ValueError(f"{name} must be finite: {value!r}")
    return result


def _normalize_key(text):
    """Normalize region/category codes for matching (strip spaces, ignore case)."""
    return str(text).strip().upper()


@lru_cache(maxsize=1)
def _load_rates():
    rates = {}
    with open(_DATA_DIR / "rates.csv", newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            region = _normalize_key(row["region"])
            rates[region] = Decimal(row["tax_pct"].strip())
    return rates


@lru_cache(maxsize=1)
def _load_exempt_categories():
    exempt = set()
    with open(_DATA_DIR / "exempt_categories.csv", newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            category = (row.get("category") or "").strip()
            if category:
                exempt.add(_normalize_key(category))
    return frozenset(exempt)


def tax_rate_pct(region):
    """Return the tax percent for a region. Unknown or missing region -> 0."""
    if region is None:
        return Decimal("0")
    return _load_rates().get(_normalize_key(region), Decimal("0"))


def is_exempt(category):
    """Return True if items of this category are not taxed."""
    return _normalize_key(category) in _load_exempt_categories()


def _round_cent(value):
    return value.quantize(_CENT, rounding=ROUND_HALF_UP)


def compute_tax(lines, region, discount_pct=0):
    """Compute the sales tax for an order.

    lines: iterable of (category, amount) pairs.
    region: customer region code, or None for an unknown customer (0% tax).
    discount_pct: customer discount percent in [0, 100].
    """
    discount = _to_decimal(discount_pct, "discount_pct")
    if discount < 0 or discount > _HUNDRED:
        raise ValueError(f"discount_pct must be between 0 and 100: {discount_pct!r}")

    taxable_amount = Decimal("0")
    for category, amount in lines:
        value = _to_decimal(amount, "amount")
        if value < 0:
            raise ValueError(f"line amount must not be negative: {amount!r}")
        if not is_exempt(category):
            taxable_amount += value

    base = taxable_amount * (_HUNDRED - discount) / _HUNDRED
    tax = base * tax_rate_pct(region) / _HUNDRED
    return _round_cent(tax)
