"""Tax module. Owned by agent2. Computes sales tax.

The data files and rules are in data_tax/ next to this file:
- data_tax/rates.csv              : region -> tax percent (e.g. TX,8.25)
- data_tax/exempt_categories.csv  : item categories that are not taxed
- data_tax/RULES.md               : tax rules

Committed team API (decision log topic tax_api, v2):
- tax_breakdown(lines, region, discount_pct=0) -> TaxResult with attributes
  taxable_cents, discount_pct, tax_pct, tax_cents
- compute_tax(lines, region, discount_pct=0) -> int cents
- lines: list of (category: str, amount_cents: int), for known items, before discount
- region: customer region string (e.g. "TX"), or None for an unknown customer (0% tax)
- discount_pct: customer discount as a percent number (10 means 10%)

Team conventions:
- Money amounts are integer cents (1250 means $12.50).
- Percentages are percent numbers (10% is 10, 8.25% is 8.25).
- A lookup that finds nothing raises KeyError.

Rules (from RULES.md):
- tax percent depends on the customer's region;
- items whose category is listed as exempt are not taxed;
- base = taxable_amount * (100 - discount_pct) / 100;
- tax = base * tax_pct / 100, rounded to the cent (half up);
- an unknown customer (region is None) pays 0% tax.
"""

from __future__ import annotations

import csv
import os
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from typing import Iterable, Optional, Sequence, Tuple, Union

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_tax")
_RATES_FILE = os.path.join(_DATA_DIR, "rates.csv")
_EXEMPT_FILE = os.path.join(_DATA_DIR, "exempt_categories.csv")

Number = Union[int, float, str, Decimal]
# A line is (category, amount_cents).
Line = Tuple[str, int]


def _load_rates(path: str) -> dict:
    rates = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            region = row["region"].strip()
            if region:
                rates[region] = Decimal(row["tax_pct"].strip())
    return rates


def _load_exempt(path: str) -> frozenset:
    with open(path, newline="", encoding="utf-8") as f:
        return frozenset(
            row["category"].strip()
            for row in csv.DictReader(f)
            if row["category"] and row["category"].strip()
        )


_RATES = _load_rates(_RATES_FILE)
_EXEMPT_CATEGORIES = _load_exempt(_EXEMPT_FILE)


@dataclass(frozen=True)
class TaxResult:
    """Breakdown of a tax calculation, for display on an invoice."""

    taxable_cents: int   # sum of non-exempt line amounts, before discount
    discount_pct: float  # customer discount, percent number
    tax_pct: float       # tax rate applied, percent number (0 for unknown customer)
    tax_cents: int       # tax amount in cents, rounded half up


def is_exempt(category: str) -> bool:
    """True if items of this category are not taxed."""
    return category in _EXEMPT_CATEGORIES


def tax_percent(region: Optional[str]) -> float:
    """Sales tax percent for a region. None (unknown customer) -> 0.

    Raises KeyError if the region is not in rates.csv.
    """
    if region is None:
        return 0.0
    return float(_RATES[region])


def tax_breakdown(
    lines: Iterable[Line],
    region: Optional[str],
    discount_pct: Number = 0,
) -> TaxResult:
    """Compute the tax for an order and return the full breakdown."""
    taxable_cents = 0
    for category, amount_cents in lines:
        if not is_exempt(category):
            taxable_cents += int(amount_cents)

    discount = Decimal(str(discount_pct))
    if region is None:
        rate = Decimal(0)
    else:
        rate = _RATES[region]  # KeyError for an unknown region

    # base = taxable_amount * (100 - discount_pct) / 100 (kept exact)
    base = Decimal(taxable_cents) * (Decimal(100) - discount) / Decimal(100)
    # tax = base * tax_pct / 100, rounded to the cent (half up)
    tax = base * rate / Decimal(100)
    tax_cents = int(tax.quantize(Decimal(1), rounding=ROUND_HALF_UP))

    return TaxResult(
        taxable_cents=taxable_cents,
        discount_pct=float(discount),
        tax_pct=float(rate),
        tax_cents=tax_cents,
    )


def compute_tax(
    lines: Iterable[Line],
    region: Optional[str],
    discount_pct: Number = 0,
) -> int:
    """Tax for an order in integer cents."""
    return tax_breakdown(lines, region, discount_pct).tax_cents
