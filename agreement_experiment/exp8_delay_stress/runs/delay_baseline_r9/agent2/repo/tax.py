"""Tax module. Owned by agent2. Computes sales tax.

The data files and rules are in data_tax/ next to this file (see data_tax/RULES.md).

Team conventions:
  * Money amounts are integers in cents (1250 means $12.50).
  * Percentages are percent numbers (10% is 10, 8.25% is 8.25).
  * A lookup that finds nothing raises KeyError.

Public API:
  compute_tax(lines, region, discount_pct) -> int   total tax in cents
  tax_rate_pct(region) -> Decimal                    percent for a region
  is_exempt(category) -> bool                        True if category is not taxed
"""

import csv
import os
from decimal import Decimal, ROUND_HALF_UP
from typing import Iterable, Optional, Tuple

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_tax")


def _load_rates(path: str) -> dict:
    """Return {region: Decimal percent} from rates.csv (columns: region, tax_pct)."""
    rates = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            region = row["region"].strip()
            # Decimal(str) keeps the value exact (e.g. 8.875 stays 8.875).
            rates[region] = Decimal(row["tax_pct"].strip())
    return rates


def _load_exempt_categories(path: str) -> frozenset:
    """Return the set of exempt category names (column: category)."""
    with open(path, newline="", encoding="utf-8") as f:
        return frozenset(
            row["category"].strip() for row in csv.DictReader(f) if row["category"].strip()
        )


_RATES = _load_rates(os.path.join(_DATA_DIR, "rates.csv"))
_EXEMPT = _load_exempt_categories(os.path.join(_DATA_DIR, "exempt_categories.csv"))


def tax_rate_pct(region: str) -> Decimal:
    """Return the sales tax percent for `region`, e.g. Decimal('8.25') for 'TX'.

    Raises KeyError if the region is not in rates.csv.
    """
    return _RATES[region]


def is_exempt(category: str) -> bool:
    """Return True if items of `category` are not taxed (listed in exempt_categories.csv)."""
    return category in _EXEMPT


def _to_decimal_percent(value) -> Decimal:
    """Convert a percent number (int, float, str or Decimal) to Decimal without float error."""
    d = Decimal(str(value))
    if not d.is_finite() or d < 0 or d > 100:
        raise ValueError(f"percent must be between 0 and 100, got {value!r}")
    return d


def compute_tax(
    lines: Iterable[Tuple[str, int]],
    region: Optional[str],
    discount_pct,
) -> int:
    """Return the total sales tax for an order, in integer cents.

    lines        : iterable of (category, amount_cents) pairs, one per line item.
                   Items in an exempt category are skipped.
    region       : customer region such as 'TX', 'NY', 'OR'. None means an
                   unknown customer, who pays 0% tax. A string region that is
                   not in rates.csv raises KeyError.
    discount_pct : customer discount as a percent number (10 means 10%).

    Rule (data_tax/RULES.md):
        taxable = sum of amounts of non-exempt lines
        base    = taxable * (100 - discount_pct) / 100
        tax     = base * tax_pct / 100, rounded to the cent (half up)

    The arithmetic is exact (Decimal), and rounding happens once, at the end.
    """
    taxable = 0
    for category, amount_cents in lines:
        if isinstance(amount_cents, bool) or not isinstance(amount_cents, int):
            raise TypeError(f"amount_cents must be an int number of cents, got {amount_cents!r}")
        if not is_exempt(category):
            taxable += amount_cents

    discount = _to_decimal_percent(discount_pct)

    if region is None:
        # Unknown customer: 0% tax.
        return 0

    rate = tax_rate_pct(region)  # KeyError if the region is unknown

    base = Decimal(taxable) * (Decimal(100) - discount) / Decimal(100)
    tax = base * rate / Decimal(100)
    return int(tax.quantize(Decimal("1"), rounding=ROUND_HALF_UP))
