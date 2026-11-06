"""Sales tax calculation.

Implements the committed decision `tax_api` v2:

* Money is integer cents at every module boundary.
* ``calculate_tax(lines, region, discount_pct) -> int`` (cents).
* ``tax_rate_percent(region) -> Decimal`` (percent, 0 if unknown).

Rules come from ``data_tax/RULES.md``; rates and exempt categories are loaded
from ``data_tax/rates.csv`` and ``data_tax/exempt_categories.csv``, located
relative to this file.
"""

from __future__ import annotations

import csv
from decimal import ROUND_HALF_UP, Decimal
from functools import lru_cache
from pathlib import Path
from typing import Iterable, Optional, Tuple, Union

_DATA_DIR = Path(__file__).resolve().parent / "data_tax"
_RATES_FILE = _DATA_DIR / "rates.csv"
_EXEMPT_FILE = _DATA_DIR / "exempt_categories.csv"

_ZERO = Decimal(0)
_HUNDRED = Decimal(100)

Line = Tuple[str, int]  # (category, amount_cents)


@lru_cache(maxsize=None)
def _load_rates() -> dict:
    """Map region code -> tax percent (Decimal) from rates.csv."""
    rates = {}
    with _RATES_FILE.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            region = row["region"].strip()
            rates[region] = Decimal(row["tax_pct"].strip())
    return rates


@lru_cache(maxsize=None)
def _load_exempt() -> frozenset:
    """Set of exempt category names from exempt_categories.csv."""
    with _EXEMPT_FILE.open(newline="", encoding="utf-8") as f:
        return frozenset(
            row["category"].strip()
            for row in csv.DictReader(f)
            if row["category"].strip()
        )


def tax_rate_percent(region: Optional[str]) -> Decimal:
    """Return the sales tax percent for ``region`` (e.g. Decimal("8.25")).

    Returns Decimal(0) for ``None`` or for a region not listed in rates.csv
    (RULES.md: an unknown customer pays 0% tax).
    """
    if region is None:
        return _ZERO
    return _load_rates().get(region, _ZERO)


def _to_discount(discount_pct: Union[int, Decimal, str, None]) -> Decimal:
    """Convert the discount percent (10 means 10%) to Decimal; None -> 0."""
    if discount_pct is None:
        return _ZERO
    if isinstance(discount_pct, float):
        # Go through str() to avoid binary float artifacts (0.1 -> 0.1000...055).
        return Decimal(str(discount_pct))
    return Decimal(discount_pct)


def calculate_tax(
    lines: Iterable[Line],
    region: Optional[str],
    discount_pct: Union[int, Decimal, str, None] = None,
) -> int:
    """Return the sales tax for an order, in integer cents.

    ``lines`` is an iterable of ``(category, amount_cents)`` tuples, one per
    line item, with pre-discount line totals in cents. Lines whose category is
    listed in exempt_categories.csv are not taxed (exact, case-sensitive match).

    Steps (RULES.md):
      1. taxable_sum = sum of amounts of non-exempt lines (cents).
      2. base = taxable_sum * (100 - discount_pct) / 100   (not rounded).
      3. tax  = base * tax_pct / 100, rounded ONCE to the cent, half up.

    An unknown or ``None`` region yields 0 tax.
    """
    exempt = _load_exempt()

    taxable_cents = 0
    for category, amount_cents in lines:
        if not isinstance(amount_cents, int) or isinstance(amount_cents, bool):
            raise TypeError(
                "amount_cents must be an int number of cents, "
                f"got {type(amount_cents).__name__}"
            )
        if category in exempt:
            continue
        taxable_cents += amount_cents

    rate = tax_rate_percent(region)
    discount = _to_discount(discount_pct)

    base = Decimal(taxable_cents) * (_HUNDRED - discount) / _HUNDRED
    tax = base * rate / _HUNDRED
    return int(tax.quantize(Decimal(1), rounding=ROUND_HALF_UP))
