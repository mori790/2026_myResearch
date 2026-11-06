"""Tax module. Owned by agent2. Computes sales tax. The data files and rules are in data_tax/ next to this file.

Conventions (team standard):
  - Money amounts are integers in cents (1250 means $12.50).
  - Percentages are percent numbers (10% is 10, 8.25% is 8.25).
  - A lookup that finds nothing raises KeyError.

Public API:
  load_rates() -> dict[str, Decimal]
      Region code -> tax percent. Read from data_tax/rates.csv.
  load_exempt_categories() -> frozenset[str]
      Categories that are not taxed. Read from data_tax/exempt_categories.csv.
  tax_pct_for_region(region) -> Decimal
      Tax percent for a region. Raises KeyError if the region is not in rates.csv.
  is_exempt(category) -> bool
      True if items of this category are not taxed.
  calculate_tax(region, lines, discount_pct) -> int
      Sales tax in cents for an order.
      region        : customer's region code, or None for an unknown customer (tax is 0).
      lines         : iterable of (category, line_amount_cents) pairs.
      discount_pct  : customer's discount in percent (e.g. 10 for 10%).

Rules (data_tax/RULES.md):
  taxable_amount = sum of line amounts whose category is not exempt
  base           = taxable_amount * (100 - discount_pct) / 100
  tax            = base * tax_pct / 100, rounded to the cent (half up)
  An unknown customer pays 0% tax.
"""

from __future__ import annotations

import csv
from decimal import Decimal, ROUND_HALF_UP
from functools import lru_cache
from pathlib import Path
from typing import Iterable, Optional, Tuple

_DATA_DIR = Path(__file__).resolve().parent / "data_tax"
_RATES_PATH = _DATA_DIR / "rates.csv"
_EXEMPT_PATH = _DATA_DIR / "exempt_categories.csv"

_HUNDRED = Decimal(100)


def _read_csv_rows(path: Path) -> list:
    with path.open(newline="", encoding="utf-8") as f:
        return [row for row in csv.DictReader(f)]


@lru_cache(maxsize=None)
def load_rates() -> dict:
    """Return {region: tax_pct as Decimal} from rates.csv."""
    rates = {}
    for row in _read_csv_rows(_RATES_PATH):
        region = row["region"].strip()
        rates[region] = Decimal(row["tax_pct"].strip())
    return rates


@lru_cache(maxsize=None)
def load_exempt_categories() -> frozenset:
    """Return the set of tax-exempt categories from exempt_categories.csv."""
    return frozenset(
        row["category"].strip() for row in _read_csv_rows(_EXEMPT_PATH) if row["category"].strip()
    )


def tax_pct_for_region(region: str) -> Decimal:
    """Return the tax percent for a region. Raises KeyError if the region has no rate."""
    rates = load_rates()
    if region not in rates:
        raise KeyError(f"no tax rate for region {region!r}")
    return rates[region]


def is_exempt(category: str) -> bool:
    """Return True if items in this category are not taxed."""
    return category in load_exempt_categories()


def calculate_tax(
    region: Optional[str],
    lines: Iterable[Tuple[str, int]],
    discount_pct,
) -> int:
    """Return the sales tax for an order, in integer cents, rounded half up.

    region        : customer's region code, or None for an unknown customer (tax 0).
    lines         : iterable of (category, line_amount_cents).
    discount_pct  : customer's discount in percent (e.g. 10 means 10%).
    """
    if region is None:
        # Unknown customer pays no tax (RULES.md).
        return 0

    tax_pct = tax_pct_for_region(region)  # KeyError if the region is unknown

    discount = Decimal(str(discount_pct))
    if discount < 0 or discount > 100:
        raise ValueError(f"discount_pct must be between 0 and 100, got {discount_pct!r}")

    taxable_amount = 0
    for category, amount_cents in lines:
        if not is_exempt(category):
            taxable_amount += int(amount_cents)

    # Exact arithmetic: base = taxable * (100 - d) / 100; tax = base * t / 100.
    base = Decimal(taxable_amount) * (_HUNDRED - discount) / _HUNDRED
    tax = base * tax_pct / _HUNDRED
    return int(tax.quantize(Decimal(1), rounding=ROUND_HALF_UP))
