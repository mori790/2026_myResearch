"""Tax module. Owned by agent2. Computes sales tax.

The data files and rules are in data_tax/ next to this file:
  - data_tax/rates.csv              region -> tax_pct (percent number, e.g. 8.25)
  - data_tax/exempt_categories.csv  categories that are not taxed
  - data_tax/RULES.md               the rules this module implements

Conventions (team standard):
  - Money amounts are integer cents (1250 means $12.50).
  - Percentages are percent numbers (10 means 10%, 8.25 means 8.25%).
  - A lookup that finds nothing raises KeyError.

Public API:
  sales_tax_cents(region, lines, discount_pct=0) -> int
  tax_rate_pct(region) -> float
  is_exempt(category) -> bool
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
            rates[region] = Decimal(row["tax_pct"].strip())
    return rates


def _load_exempt(path):
    exempt = set()
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            category = (row.get("category") or "").strip()
            if category:
                exempt.add(category)
    return exempt


_RATES = _load_rates(_RATES_PATH)          # region -> Decimal percent
_EXEMPT_CATEGORIES = _load_exempt(_EXEMPT_PATH)


def tax_rate_pct(region):
    """Return the sales tax percent for a region code (e.g. 'TX' -> 8.25).

    Raises KeyError if the region is not in rates.csv.
    """
    return float(_RATES[region])


def is_exempt(category):
    """Return True if items in this category are not taxed."""
    return category in _EXEMPT_CATEGORIES


def sales_tax_cents(region, lines, discount_pct=0):
    """Compute the sales tax for one order, in integer cents.

    region:       customer's region code (e.g. 'TX'). None means the customer
                  is unknown, which pays 0% tax. An unknown region code that is
                  not None raises KeyError.
    lines:        iterable of (category, amount_cents) pairs, one per order line,
                  where amount_cents is the line total (after quantity).
    discount_pct: customer's discount percent (e.g. 10 means 10% off).

    Rule (data_tax/RULES.md):
      taxable    = sum of amounts whose category is not exempt
      base       = taxable * (100 - discount_pct) / 100
      tax        = base * tax_pct / 100, rounded to the cent (half up)

    Arithmetic is exact (Decimal); the only rounding is the final one.
    """
    discount = Decimal(str(discount_pct))
    if not (Decimal(0) <= discount <= Decimal(100)):
        raise ValueError("discount_pct must be between 0 and 100, got %r" % (discount_pct,))

    if region is None:
        return 0
    rate = _RATES[region]  # KeyError for an unknown region

    taxable = 0
    for category, amount_cents in lines:
        if not is_exempt(category):
            taxable += int(amount_cents)

    base = Decimal(taxable) * (Decimal(100) - discount) / Decimal(100)
    tax = base * rate / Decimal(100)
    return int(tax.quantize(Decimal("1"), rounding=ROUND_HALF_UP))
