"""Tax module. Owned by agent2. Computes sales tax.

The data files and rules are in data_tax/ next to this file:
  - data_tax/rates.csv             region -> tax percent
  - data_tax/exempt_categories.csv categories that are not taxed
  - data_tax/RULES.md              the rules implemented here

Public API:
  compute_tax(region, lines, discount_pct=Decimal('0')) -> (Decimal tax_pct, int tax_cents)
  tax_rate(region) -> Decimal
  is_exempt(category) -> bool

Money is integer cents; percents are Decimal. The tax computation is done in
Decimal so no binary floating-point rounding errors appear.
"""

import csv
import os
from decimal import Decimal, ROUND_HALF_UP
from typing import Iterable, Tuple

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_tax")
_RATES_PATH = os.path.join(_DATA_DIR, "rates.csv")
_EXEMPT_PATH = os.path.join(_DATA_DIR, "exempt_categories.csv")

_HUNDRED = Decimal("100")

def _to_decimal(value) -> Decimal:
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def _normalize_key(value: str) -> str:
    return str(value).strip().casefold()


def _load_rates(path: str) -> dict:
    rates = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            region = (row.get("region") or "").strip()
            pct = (row.get("tax_pct") or "").strip()
            if region and pct:
                rates[_normalize_key(region)] = Decimal(pct)
    return rates


def _load_exempt(path: str) -> frozenset:
    exempt = set()
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            category = (row.get("category") or "").strip()
            if category:
                exempt.add(_normalize_key(category))
    return frozenset(exempt)


_RATES = _load_rates(_RATES_PATH)
_EXEMPT = _load_exempt(_EXEMPT_PATH)


def tax_rate(region: str) -> Decimal:
    """Return the tax percent for a customer region (e.g. 'TX' -> 8.25).

    Unknown regions (or None) pay 0%.
    """
    if region is None:
        return Decimal("0")
    return _RATES.get(_normalize_key(region), Decimal("0"))


def is_exempt(category: str) -> bool:
    """Return True if items in this category are not taxed."""
    if category is None:
        return False
    return _normalize_key(category) in _EXEMPT


def compute_tax(
    region: str,
    lines: Iterable[Tuple[str, int]],
    discount_pct: Decimal = Decimal("0"),
) -> Tuple[Decimal, int]:
    """Compute the sales tax for an order.

    region:       customer region code, e.g. 'TX'. Unknown region -> 0%.
    lines:        iterable of (category, line_cents) pairs. line_cents is the
                  pre-discount line total in integer cents.
    discount_pct: customer discount percent as Decimal, e.g. Decimal('10') = 10%.
                  Must be in [0, 100].

    Rules (see data_tax/RULES.md):
      taxable    = sum of line_cents whose category is not exempt
      base       = taxable * (100 - discount_pct) / 100
      tax        = base * tax_pct / 100, rounded to the cent (half up)

    Rounding is applied once, to the final tax only.

    Returns (tax_pct, tax_cents): the rate applied (Decimal) and the tax in
    integer cents. Unknown region -> (Decimal('0'), 0).
    """
    discount = _to_decimal(discount_pct)
    if discount < 0 or discount > _HUNDRED:
        raise ValueError(f"discount_pct must be between 0 and 100, got {discount_pct!r}")

    rate = tax_rate(region)

    taxable_cents = Decimal("0")
    for category, line_cents in lines:
        if not is_exempt(category):
            taxable_cents += _to_decimal(line_cents)

    base = taxable_cents * (_HUNDRED - discount) / _HUNDRED
    tax_cents = (base * rate / _HUNDRED).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    return rate, int(tax_cents)
