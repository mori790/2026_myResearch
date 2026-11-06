"""Tax module. Owned by agent2. Computes sales tax.

The data files and rules are in data_tax/ next to this file
(rates.csv, exempt_categories.csv, RULES.md).

Team units (coding standard):
  - Money amounts are integers in cents (1250 means $12.50).
  - Percentages are percent numbers (10 means 10%, 8.25 means 8.25%).
  - A lookup that finds nothing raises KeyError.

Public API:
  get_tax_pct(region)                      -> float   (KeyError if region unknown)
  is_exempt(category)                      -> bool
  compute_tax(lines, region, discount_pct) -> int     (cents)

  lines        : iterable of (category: str, amount_cents: int)
  region       : customer region string, or None for an unknown customer (0% tax)
  discount_pct : customer discount as a percent number (0 to 100)
"""

import csv
import os
from decimal import Decimal, ROUND_HALF_UP
from typing import Iterable, Optional, Tuple

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_tax")
_RATES_PATH = os.path.join(_DATA_DIR, "rates.csv")
_EXEMPT_PATH = os.path.join(_DATA_DIR, "exempt_categories.csv")


def _load_rates(path: str) -> dict:
    rates = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            region = row["region"].strip()
            rates[region] = Decimal(row["tax_pct"].strip())
    return rates


def _load_exempt(path: str) -> frozenset:
    categories = set()
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            categories.add(row["category"].strip())
    return frozenset(categories)


_RATES = _load_rates(_RATES_PATH)            # region -> Decimal percent
_EXEMPT = _load_exempt(_EXEMPT_PATH)         # set of exempt category names


def get_tax_pct(region: str) -> float:
    """Return the sales tax percent for a region, e.g. 'TX' -> 8.25.

    Raises KeyError if the region is not in rates.csv.
    """
    return float(_RATES[region])


def is_exempt(category: str) -> bool:
    """True if items in this category are not taxed."""
    return category in _EXEMPT


def _to_decimal_pct(discount_pct) -> Decimal:
    if isinstance(discount_pct, bool) or not isinstance(discount_pct, (int, float, Decimal)):
        raise TypeError("discount_pct must be a percent number, e.g. 10 for 10%")
    # Going through str() avoids binary float noise (8.25 stays exactly 8.25).
    value = Decimal(str(discount_pct))
    if value < 0 or value > 100:
        raise ValueError("discount_pct must be between 0 and 100 (percent)")
    return value


def compute_tax(
    lines: Iterable[Tuple[str, int]],
    region: Optional[str],
    discount_pct,
) -> int:
    """Return the sales tax for an order, in integer cents.

    Steps (see data_tax/RULES.md):
      1. taxable_amount = sum of line amounts whose category is not exempt.
      2. base = taxable_amount * (100 - discount_pct) / 100
      3. tax  = base * tax_pct / 100, rounded to the cent (half up).

    region=None means an unknown customer, who pays 0% tax.
    """
    taxable_cents = 0
    for category, amount_cents in lines:
        if isinstance(amount_cents, bool) or not isinstance(amount_cents, int):
            raise TypeError(
                "line amounts must be integer cents, got %r (dollar floats are not allowed)"
                % (amount_cents,)
            )
        if amount_cents < 0:
            raise ValueError("line amounts must not be negative")
        if not is_exempt(category):
            taxable_cents += amount_cents

    if region is None:
        return 0

    tax_pct = _RATES[region]  # KeyError if the region is unknown
    discount = _to_decimal_pct(discount_pct)

    base = Decimal(taxable_cents) * (Decimal(100) - discount) / Decimal(100)
    tax = base * tax_pct / Decimal(100)
    return int(tax.quantize(Decimal("1"), rounding=ROUND_HALF_UP))
