"""Tax module. Owned by agent2. Computes sales tax.

The data files and rules are in data_tax/ next to this file (rates.csv,
exempt_categories.csv, RULES.md).

API (team decision `tax_api`, see `agree.py lookup tax_api`):
  Units: money = int cents (1250 means $12.50);
         percent = percent number (8.25 means 8.25%, 10 means 10%).
  TaxLine(category: str, amount_cents: int)
  get_tax_pct(region: str) -> float            # KeyError if region is unknown
  is_exempt(category: str) -> bool
  compute_tax(lines, region, discount_pct=0) -> int   # cents
      region=None means unknown customer -> 0 tax.
      Unknown region -> KeyError.
"""

import csv
import os
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from typing import Iterable, Optional

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_tax")
_RATES_PATH = os.path.join(_DATA_DIR, "rates.csv")
_EXEMPT_PATH = os.path.join(_DATA_DIR, "exempt_categories.csv")


def _load_rates(path: str) -> dict:
    rates = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            rates[row["region"].strip()] = Decimal(row["tax_pct"].strip())
    return rates


def _load_exempt(path: str) -> frozenset:
    with open(path, newline="", encoding="utf-8") as f:
        return frozenset(
            row["category"].strip()
            for row in csv.DictReader(f)
            if row["category"].strip()
        )


_RATES = _load_rates(_RATES_PATH)          # region -> Decimal percent
_EXEMPT = _load_exempt(_EXEMPT_PATH)       # set of exempt categories


@dataclass(frozen=True)
class TaxLine:
    """One invoice line that may be taxed. amount_cents is an int number of cents."""

    category: str
    amount_cents: int

    def __post_init__(self):
        # Guard against float dollars (e.g. pricing.get_price) being passed in by mistake.
        if not isinstance(self.amount_cents, int) or isinstance(self.amount_cents, bool):
            raise TypeError(
                f"amount_cents must be int cents, got {type(self.amount_cents).__name__}"
            )


def get_tax_pct(region: str) -> float:
    """Return the tax percent for a region (e.g. 'TX' -> 8.25). Raises KeyError if unknown."""
    return float(_RATES[region])


def is_exempt(category: str) -> bool:
    """True if items in this category are not taxed."""
    return category in _EXEMPT


def compute_tax(
    lines: Iterable[TaxLine],
    region: Optional[str],
    discount_pct: float = 0,
) -> int:
    """Return the sales tax in int cents.

    base = taxable_amount * (100 - discount_pct) / 100
    tax  = base * tax_pct / 100, rounded to the cent (half up).
    taxable_amount = sum of amounts of non-exempt lines.
    Unknown customer (region is None) pays 0 tax.
    """
    if region is None:
        return 0
    rate = _RATES[region]  # KeyError for unknown region

    discount = Decimal(str(discount_pct))
    if discount < 0 or discount > 100:
        raise ValueError(f"discount_pct must be between 0 and 100, got {discount_pct}")

    taxable = sum(line.amount_cents for line in lines if not is_exempt(line.category))

    # Exact decimal arithmetic; only the final result is rounded.
    base = Decimal(taxable) * (Decimal(100) - discount) / Decimal(100)
    tax = base * rate / Decimal(100)
    return int(tax.quantize(Decimal("1"), rounding=ROUND_HALF_UP))
