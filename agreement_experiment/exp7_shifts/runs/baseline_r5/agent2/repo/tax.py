"""Tax module. Owned by agent2. Computes sales tax.

The data files and rules are in data_tax/ next to this file (see data_tax/RULES.md).

Team coding standard (all functions in this module follow it):
  * Money amounts are integers in cents (1250 means $12.50).
  * Percentages are percent numbers (10 means 10%, 8.25 means 8.25%).
  * A lookup that finds nothing raises KeyError.

Public API:
  get_tax_pct(region)                  -> float   tax percent for a region (KeyError if unknown)
  is_exempt(category)                  -> bool    True if the category is listed in exempt_categories.csv
  taxable_amount_cents(lines)          -> int     sum of line amounts whose category is not exempt
  compute_tax_cents(lines, region, discount_pct=0) -> int
                                                  sales tax in cents for an order
"""

import csv
import os
from decimal import Decimal, ROUND_HALF_UP

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_tax")
_RATES_PATH = os.path.join(_DATA_DIR, "rates.csv")
_EXEMPT_PATH = os.path.join(_DATA_DIR, "exempt_categories.csv")


def _load_rates(path):
    rates = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            region = row["region"].strip()
            # Keep the exact decimal value from the file (e.g. "8.875") to avoid float error.
            rates[region] = Decimal(row["tax_pct"].strip())
    return rates


def _load_exempt(path):
    exempt = set()
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            category = row["category"].strip()
            if category:
                exempt.add(category)
    return frozenset(exempt)


_RATES = _load_rates(_RATES_PATH)            # region -> Decimal percent number
_EXEMPT_CATEGORIES = _load_exempt(_EXEMPT_PATH)


def get_tax_pct(region):
    """Return the tax percent number for a customer region (e.g. 'TX' -> 8.25).

    region=None means an unknown customer, who pays 0% tax (RULES.md).
    Raises KeyError if a known region has no rate in rates.csv.
    """
    if region is None:
        return 0.0
    if region not in _RATES:
        raise KeyError(f"no tax rate for region {region!r}")
    return float(_RATES[region])


def is_exempt(category):
    """True if items of this category are not taxed (exempt_categories.csv)."""
    return category in _EXEMPT_CATEGORIES


def _check_cents(value, what):
    # Reject floats (e.g. dollar amounts) so a unit mismatch fails loudly.
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{what} must be an int number of cents, got {value!r}")
    if value < 0:
        raise ValueError(f"{what} must not be negative, got {value}")
    return value


def taxable_amount_cents(lines):
    """Sum of line amounts (in cents) whose category is not exempt.

    lines: iterable of (category, amount_cents) pairs.
    """
    total = 0
    for category, amount in lines:
        amount = _check_cents(amount, "line amount")
        if not is_exempt(category):
            total += amount
    return total


def compute_tax_cents(lines, region, discount_pct=0):
    """Sales tax in integer cents for an order.

    lines:        iterable of (category, amount_cents) pairs.
    region:       customer region (e.g. 'TX'); None for an unknown customer (0% tax).
    discount_pct: customer discount as a percent number (e.g. 10 means 10%).

    Rules (data_tax/RULES.md):
      taxable   = sum of non-exempt line amounts
      base      = taxable * (100 - discount_pct) / 100
      tax       = base * tax_pct / 100, rounded to the cent (half up)
    """
    taxable = taxable_amount_cents(lines)

    if isinstance(discount_pct, bool) or not isinstance(discount_pct, (int, float, Decimal)):
        raise TypeError(f"discount_pct must be a percent number, got {discount_pct!r}")
    if not 0 <= discount_pct <= 100:
        raise ValueError(f"discount_pct must be between 0 and 100, got {discount_pct}")

    tax_pct = Decimal(str(get_tax_pct(region)))
    discount = Decimal(str(discount_pct))

    # Exact decimal arithmetic; quantize only the final amount.
    tax = Decimal(taxable) * (Decimal(100) - discount) / Decimal(100) * tax_pct / Decimal(100)
    return int(tax.quantize(Decimal("1"), rounding=ROUND_HALF_UP))
