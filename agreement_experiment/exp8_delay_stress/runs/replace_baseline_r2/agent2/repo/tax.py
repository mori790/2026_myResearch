"""Tax module. Owned by agent2. Computes sales tax.

The data files and rules are in data_tax/ next to this file (see data_tax/RULES.md).

Conventions (team standard):
  * Money amounts are integers in cents (1250 means $12.50).
  * Percentages are percent numbers (10% is 10, 8.25% is 8.25).
  * A lookup that finds nothing raises KeyError.

Public API
----------
compute_tax(lines, region, discount_pct=0) -> TaxResult
    Main entry point. ``lines`` is an iterable of ``(category, amount_cents)``
    pairs, one per order line. ``region`` is the customer's region code
    (e.g. "TX"), or ``None`` for an unknown customer (which pays 0% tax).
    ``discount_pct`` is the customer's discount in percent (0..100).

tax_percent(region) -> Decimal
    Tax percent for a region. ``None`` -> 0. Unknown region -> KeyError.

is_exempt(category) -> bool
    True if the category is listed in exempt_categories.csv.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path
from typing import Iterable, Optional, Tuple

_DATA_DIR = Path(__file__).resolve().parent / "data_tax"

__all__ = ["TaxResult", "compute_tax", "tax_percent", "is_exempt"]


def _load_rates(path: Path) -> dict:
    rates = {}
    with path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            region = row["region"].strip()
            rates[region] = Decimal(row["tax_pct"].strip())
    return rates


def _load_exempt(path: Path) -> frozenset:
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return frozenset(row["category"].strip() for row in reader if row.get("category"))


_RATES = _load_rates(_DATA_DIR / "rates.csv")
_EXEMPT = _load_exempt(_DATA_DIR / "exempt_categories.csv")


@dataclass(frozen=True)
class TaxResult:
    """Breakdown of a tax computation. All money fields are integer cents."""

    taxable_cents: int      # sum of non-exempt line amounts, before discount
    discount_pct: Decimal   # customer discount in percent
    tax_pct: Decimal        # tax rate in percent (0 for unknown customer)
    tax_cents: int          # final tax, rounded to the cent (half up)


def is_exempt(category: str) -> bool:
    """Return True if items of this category are not taxed."""
    return category.strip() in _EXEMPT


def tax_percent(region: Optional[str]) -> Decimal:
    """Return the tax percent for a customer region.

    ``None`` means an unknown customer, who pays 0%.
    An unrecognised region code raises KeyError.
    """
    if region is None:
        return Decimal(0)
    key = region.strip()
    if key not in _RATES:
        raise KeyError(f"no tax rate for region {region!r}")
    return _RATES[key]


def compute_tax(
    lines: Iterable[Tuple[str, int]],
    region: Optional[str],
    discount_pct=0,
) -> TaxResult:
    """Compute sales tax for an order.

    Steps (from data_tax/RULES.md):
      1. Taxable amount = sum of line amounts whose category is not exempt.
      2. base = taxable * (100 - discount_pct) / 100
      3. tax  = base * tax_pct / 100, rounded to the cent (half up).
    """
    taxable = 0
    for category, amount_cents in lines:
        if isinstance(amount_cents, bool) or not isinstance(amount_cents, int):
            raise TypeError(f"amount must be an integer number of cents, got {amount_cents!r}")
        if category is None or not is_exempt(category):
            taxable += amount_cents

    discount = Decimal(str(discount_pct))
    if not (Decimal(0) <= discount <= Decimal(100)):
        raise ValueError(f"discount_pct must be between 0 and 100, got {discount_pct!r}")

    rate = tax_percent(region)

    base = Decimal(taxable) * (Decimal(100) - discount) / Decimal(100)
    tax = base * rate / Decimal(100)
    tax_cents = int(tax.quantize(Decimal(1), rounding=ROUND_HALF_UP))

    return TaxResult(
        taxable_cents=taxable,
        discount_pct=discount,
        tax_pct=rate,
        tax_cents=tax_cents,
    )
