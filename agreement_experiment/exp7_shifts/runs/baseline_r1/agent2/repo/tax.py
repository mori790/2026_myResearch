"""Tax module. Owned by agent2. Computes sales tax.

The data files and rules are in data_tax/ next to this file.

Team convention (used everywhere in this module):
  * money amounts are integers in cents (1250 means $12.50)
  * percentages are percent numbers (10 means 10%, 8.25 means 8.25%)
  * a lookup that finds nothing raises KeyError

Public API:
  calculate_tax(lines, region, discount_pct=0) -> int   tax in cents
  tax_rate_pct(region) -> Decimal                        rate for a region, e.g. TX -> 8.25
  is_exempt(category) -> bool                            True if the category is not taxed

Rules (data_tax/RULES.md):
  base = taxable_amount * (100 - discount_pct) / 100
  tax  = base * tax_pct / 100, rounded to the cent (half up)
  Only lines whose category is NOT exempt count toward taxable_amount.
  An unknown customer (region None) pays 0% tax.
"""

from __future__ import annotations

import csv
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path
from typing import Dict, Iterable, Optional, Tuple, Union

__all__ = ["calculate_tax", "tax_rate_pct", "is_exempt"]

_DATA_DIR = Path(__file__).resolve().parent / "data_tax"

Number = Union[int, float, Decimal]


def _norm(text: str) -> str:
    return str(text).strip().upper()


def _load_rates(path: Path) -> Dict[str, Decimal]:
    rates: Dict[str, Decimal] = {}
    with path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            region = _norm(row["region"])
            if not region:
                raise ValueError(f"{path.name}: empty region")
            if region in rates:
                raise ValueError(f"{path.name}: duplicate region {region!r}")
            rates[region] = Decimal(row["tax_pct"].strip())
    return rates


def _load_exempt(path: Path) -> frozenset:
    exempt = set()
    with path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            category = _norm(row["category"])
            if category:
                exempt.add(category)
    return frozenset(exempt)


_RATES: Dict[str, Decimal] = _load_rates(_DATA_DIR / "rates.csv")
_EXEMPT = _load_exempt(_DATA_DIR / "exempt_categories.csv")


def _check_cents(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"amount must be an integer number of cents, got {value!r}")
    return value


def _check_percent(value: object, name: str) -> Decimal:
    if isinstance(value, bool) or not isinstance(value, (int, float, Decimal)):
        raise TypeError(f"{name} must be a percent number, got {value!r}")
    pct = value if isinstance(value, Decimal) else Decimal(str(value))
    if not (Decimal(0) <= pct <= Decimal(100)):
        raise ValueError(f"{name} must be between 0 and 100, got {value!r}")
    return pct


def is_exempt(category: str) -> bool:
    """True if items in this category are not taxed (see exempt_categories.csv)."""
    return _norm(category) in _EXEMPT


def tax_rate_pct(region: Optional[str]) -> Decimal:
    """Tax percent for a customer region (rates.csv).

    region None means an unknown customer, which pays 0%.
    A region that is not in rates.csv raises KeyError, so missing tax data is
    reported instead of silently charging nothing.
    """
    if region is None:
        return Decimal(0)
    key = _norm(region)
    if key not in _RATES:
        raise KeyError(f"no tax rate for region {region!r}")
    return _RATES[key]


def calculate_tax(
    lines: Iterable[Tuple[str, int]],
    region: Optional[str],
    discount_pct: Number = 0,
) -> int:
    """Return the sales tax in integer cents.

    lines        iterable of (category, amount_cents) pairs for the order lines.
    region       customer region such as "TX"; None for an unknown customer (0%).
    discount_pct customer discount as a percent number (10 means 10%).
                 It reduces only the taxable amount, not the exempt lines.
    """
    discount = _check_percent(discount_pct, "discount_pct")
    rate = tax_rate_pct(region)

    taxable_cents = 0
    for category, amount_cents in lines:
        amount = _check_cents(amount_cents)
        if not is_exempt(category):
            taxable_cents += amount

    base = Decimal(taxable_cents) * (Decimal(100) - discount) / Decimal(100)
    tax = base * rate / Decimal(100)
    return int(tax.quantize(Decimal(1), rounding=ROUND_HALF_UP))
