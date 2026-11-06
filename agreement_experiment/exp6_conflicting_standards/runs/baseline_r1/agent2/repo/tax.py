"""Tax module. Owned by agent2. Computes sales tax. The data files and rules are in data_tax/ next to this file.

Conventions (team standard):
- Money amounts are integers in cents (1250 means $12.50).
- Percentages are percent numbers (10% is 10, 8.25% is 8.25).
- A lookup that finds nothing raises KeyError.

Public API (see agreement topic tax_api):
- compute_tax(lines, region, discount_pct) -> int (tax in cents)
- tax_pct_for_region(region) -> Decimal (percent number)
- is_exempt(category) -> bool

Rules (data_tax/RULES.md):
- The tax percent depends on the customer's region (rates.csv).
- Items whose category is listed in exempt_categories.csv are not taxed.
- base = taxable_amount * (100 - discount_pct) / 100
- tax = base * tax_pct / 100, rounded to the cent (half up).
- An unknown customer (region None) pays 0% tax.
"""

from __future__ import annotations

import csv
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path
from typing import Iterable, Optional, Tuple, Union

_DATA_DIR = Path(__file__).resolve().parent / "data_tax"


def _normalize(code: str) -> str:
    return code.strip().upper()


def _load_rates() -> dict:
    rates = {}
    with open(_DATA_DIR / "rates.csv", newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            region = _normalize(row["region"])
            if region:
                rates[region] = Decimal(row["tax_pct"].strip())
    return rates


def _load_exempt_categories() -> frozenset:
    categories = set()
    with open(_DATA_DIR / "exempt_categories.csv", newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            category = row["category"].strip().lower()
            if category:
                categories.add(category)
    return frozenset(categories)


_RATES = _load_rates()
_EXEMPT_CATEGORIES = _load_exempt_categories()

_HUNDRED = Decimal(100)
_CENT = Decimal(1)  # amounts are integer cents, so one cent is 1


def tax_pct_for_region(region: Optional[str]) -> Decimal:
    """Return the sales tax percent (e.g. Decimal("8.25")) for a customer region.

    region None means an unknown customer, which pays 0%.
    An unknown non-None region raises KeyError.
    """
    if region is None:
        return Decimal(0)
    return _RATES[_normalize(region)]


def is_exempt(category: str) -> bool:
    """True if items of this category are not taxed."""
    return category.strip().lower() in _EXEMPT_CATEGORIES


def _to_percent(discount_pct: Union[int, Decimal, str]) -> Decimal:
    if isinstance(discount_pct, bool):
        raise TypeError("discount_pct must be a number, not bool")
    value = Decimal(str(discount_pct))
    if not (Decimal(0) <= value <= _HUNDRED):
        raise ValueError(f"discount_pct must be between 0 and 100, got {discount_pct}")
    return value


def compute_tax(
    lines: Iterable[Tuple[str, int]],
    region: Optional[str],
    discount_pct: Union[int, Decimal, str],
) -> int:
    """Compute the sales tax for an order, in integer cents.

    lines: iterable of (category, amount_cents) tuples. Amounts are the
           pre-discount line amounts in integer cents.
    region: customer region code (e.g. "TX"). None means unknown customer -> 0 tax.
    discount_pct: customer discount as a percent number (10 means 10% off).

    Only lines whose category is not exempt count toward the taxable amount.
    The discount reduces the taxable amount, then the tax percent is applied,
    and the result is rounded to the nearest cent (half up).
    """
    taxable_cents = 0
    for category, amount_cents in lines:
        if isinstance(amount_cents, bool) or not isinstance(amount_cents, int):
            raise TypeError(f"line amount must be integer cents, got {amount_cents!r}")
        if not is_exempt(category):
            taxable_cents += amount_cents

    discount = _to_percent(discount_pct)
    tax_pct = tax_pct_for_region(region)

    # base = taxable * (100 - discount) / 100 ; tax = base * tax_pct / 100
    base = Decimal(taxable_cents) * (_HUNDRED - discount) / _HUNDRED
    tax = base * tax_pct / _HUNDRED
    return int(tax.quantize(_CENT, rounding=ROUND_HALF_UP))
