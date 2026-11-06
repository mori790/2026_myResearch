"""Tax module. Owned by agent2. Computes sales tax.

The data files and rules are in data_tax/ next to this file (see data_tax/RULES.md).

Team conventions (committed decisions money_units v1 and tax_interface v2):
- Money amounts are integers in cents (1250 means $12.50).
- Percentages are percent numbers (8.25 means 8.25%).
- A lookup that finds nothing raises KeyError, except that an unknown
  customer (region=None) pays 0% tax, as RULES.md specifies.
"""

import csv
import os
from decimal import Decimal, ROUND_HALF_UP

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_tax")


def _load_rates(path):
    rates = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            region = row["region"].strip()
            rates[region] = Decimal(row["tax_pct"].strip())
    return rates


def _load_exempt(path):
    with open(path, newline="", encoding="utf-8") as f:
        return {row["category"].strip() for row in csv.DictReader(f) if row["category"].strip()}


_RATES = _load_rates(os.path.join(_DATA_DIR, "rates.csv"))
_EXEMPT_CATEGORIES = _load_exempt(os.path.join(_DATA_DIR, "exempt_categories.csv"))


def rate_pct(region):
    """Return the sales tax rate for a region as a percent number (e.g. Decimal('8.25')).

    Raises KeyError if the region is not in rates.csv.
    """
    return _RATES[region]


def is_exempt(category):
    """True if items of this category are not taxed (exempt_categories.csv)."""
    return category in _EXEMPT_CATEGORIES


def compute_tax(region, discount_pct, lines):
    """Return the sales tax for one order, in integer cents.

    region       -- region code such as "TX", or None for an unknown customer (tax is 0).
    discount_pct -- customer discount as a percent number (10 means 10% off); 0 if none.
    lines        -- iterable of (category, amount_cents) for each known line item.

    Rules (RULES.md):
      taxable    = sum of amounts of lines whose category is not exempt
      base       = taxable * (100 - discount_pct) / 100
      tax        = base * tax_pct / 100, rounded half up to whole cents.
    Raises KeyError if region is a non-None string that is not in rates.csv.
    """
    if region is None:
        return 0

    tax_pct = rate_pct(region)
    discount = Decimal(str(discount_pct))

    taxable = 0
    for category, amount_cents in lines:
        if not is_exempt(category):
            taxable += int(amount_cents)

    base = Decimal(taxable) * (Decimal(100) - discount) / Decimal(100)
    tax = base * tax_pct / Decimal(100)
    return int(tax.quantize(Decimal("1"), rounding=ROUND_HALF_UP))
