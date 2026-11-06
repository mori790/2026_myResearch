"""Tax module. Owned by agent2. Computes sales tax.

The data files and rules are in data_tax/ next to this file:
  - data_tax/rates.csv              region -> tax_pct (percent number, e.g. 8.25)
  - data_tax/exempt_categories.csv  categories that are not taxed
  - data_tax/RULES.md               the tax rules

Team conventions:
  - Money amounts are integers in cents (1250 means $12.50).
  - Percentages are percent numbers (10% is 10, 8.25% is 8.25).
  - A lookup that finds nothing raises KeyError.

Public API:
  tax_for_order(lines, region, discount_pct) -> TaxResult
  tax_pct_for_region(region) -> float
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from functools import lru_cache
from pathlib import Path
from typing import Iterable, Optional, Tuple

_DATA_DIR = Path(__file__).resolve().parent / "data_tax"
_RATES_PATH = _DATA_DIR / "rates.csv"
_EXEMPT_PATH = _DATA_DIR / "exempt_categories.csv"

_HUNDRED = Decimal(100)


@dataclass(frozen=True)
class TaxResult:
    """Tax breakdown for one order.

    tax_pct:       the percent rate applied (0.0 for an unknown customer).
    exempt_cents:  sum of line amounts in exempt categories (before discount).
    taxable_cents: sum of line amounts in taxable categories (before discount).
    tax_cents:     tax in integer cents, rounded half up.
    """

    tax_pct: float
    exempt_cents: int
    taxable_cents: int
    tax_cents: int


@lru_cache(maxsize=1)
def _load_rates() -> dict:
    rates = {}
    with _RATES_PATH.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            region = row["region"].strip()
            rates[region] = Decimal(row["tax_pct"].strip())
    return rates


@lru_cache(maxsize=1)
def _load_exempt_categories() -> frozenset:
    with _EXEMPT_PATH.open(newline="", encoding="utf-8") as f:
        return frozenset(
            row["category"].strip() for row in csv.DictReader(f) if row["category"].strip()
        )


def _rate_decimal(region: Optional[str]) -> Decimal:
    # Unknown customer (region is None) pays 0% tax, per RULES.md.
    if region is None:
        return Decimal(0)
    rates = _load_rates()
    if region not in rates:
        raise KeyError(f"no tax rate for region {region!r}")
    return rates[region]


def tax_pct_for_region(region: Optional[str]) -> float:
    """Return the tax percent (e.g. 8.25) for a region code.

    region=None (unknown customer) returns 0.0.
    An unknown region code raises KeyError.
    """
    return float(_rate_decimal(region))


def _check_cents(value: object, what: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{what} must be an int number of cents, got {value!r}")
    return value


def _split_lines(lines: Iterable[Tuple[str, int]]) -> Tuple[int, int]:
    """Return (exempt_cents, taxable_cents) for an iterable of (category, amount_cents)."""
    exempt_categories = _load_exempt_categories()
    exempt = 0
    taxable = 0
    for category, amount_cents in lines:
        amount = _check_cents(amount_cents, "line amount")
        if amount < 0:
            raise ValueError(f"line amount must be non-negative, got {amount}")
        if category.strip() in exempt_categories:
            exempt += amount
        else:
            taxable += amount
    return exempt, taxable


def tax_for_order(
    lines: Iterable[Tuple[str, int]],
    region: Optional[str],
    discount_pct: float,
) -> TaxResult:
    """Compute the sales tax for an order.

    lines:        iterable of (category, amount_cents). amount_cents is the line
                  total (unit price x quantity) before discount and tax.
    region:       customer region code such as 'TX'. None means an unknown
                  customer, which pays 0% tax. An unknown code raises KeyError.
    discount_pct: customer discount as a percent number (10 means 10%).

    Rules (data_tax/RULES.md):
      taxable_amount = sum of non-exempt line amounts
      base           = taxable_amount * (100 - discount_pct) / 100
      tax            = base * tax_pct / 100, rounded to the cent (half up)
    """
    exempt_cents, taxable_cents = _split_lines(lines)

    if isinstance(discount_pct, bool) or not isinstance(discount_pct, (int, float, Decimal)):
        raise TypeError(f"discount_pct must be a number (percent), got {discount_pct!r}")
    discount = Decimal(str(discount_pct))
    if not Decimal(0) <= discount <= _HUNDRED:
        raise ValueError(f"discount_pct must be between 0 and 100, got {discount_pct!r}")

    rate = _rate_decimal(region)

    base = Decimal(taxable_cents) * (_HUNDRED - discount) / _HUNDRED
    tax = base * rate / _HUNDRED
    tax_cents = int(tax.quantize(Decimal(1), rounding=ROUND_HALF_UP))

    return TaxResult(
        tax_pct=float(rate),
        exempt_cents=exempt_cents,
        taxable_cents=taxable_cents,
        tax_cents=tax_cents,
    )
