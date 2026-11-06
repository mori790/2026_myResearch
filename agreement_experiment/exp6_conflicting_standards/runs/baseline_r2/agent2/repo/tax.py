"""Tax module. Owned by agent2. Computes sales tax.

The data files and rules are in data_tax/ next to this file.

Team conventions:
  - Money amounts are integers in cents (1250 means $12.50).
  - Percentages are percent numbers (10 means 10%, 8.25 means 8.25%).
  - A lookup that finds nothing raises KeyError.

Public API:
  tax_pct(region)                         -> Decimal percent for a region
  is_exempt(category)                     -> bool
  taxable_amount(lines)                   -> int cents
  compute_tax(region, lines, discount_pct=0) -> int cents (tax only)

Where:
  region        : str region code (e.g. "TX"), or None for an unknown customer
                  (unknown customer pays 0% tax).
  lines         : iterable of (category, amount_cents) pairs, one per line item.
  discount_pct  : customer discount as a percent number (e.g. 10 for 10%).
"""

import csv
import os
from decimal import Decimal, ROUND_HALF_UP

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_tax")
_RATES_PATH = os.path.join(_DATA_DIR, "rates.csv")
_EXEMPT_PATH = os.path.join(_DATA_DIR, "exempt_categories.csv")

_HUNDRED = Decimal("100")


def _load_rates(path=_RATES_PATH):
    rates = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            region = row["region"].strip()
            rates[region] = Decimal(row["tax_pct"].strip())
    return rates


def _load_exempt(path=_EXEMPT_PATH):
    exempt = set()
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            category = (row.get("category") or "").strip()
            if category:
                exempt.add(category)
    return exempt


_RATES = _load_rates()
_EXEMPT = _load_exempt()


def tax_pct(region):
    """Return the tax percent (Decimal) for a region.

    None (unknown customer) -> 0. An unknown region code raises KeyError.
    """
    if region is None:
        return Decimal("0")
    return _RATES[region]


def is_exempt(category):
    """True if items in this category are not taxed."""
    return category in _EXEMPT


def taxable_amount(lines):
    """Sum (in cents) of the line amounts whose category is not exempt.

    lines: iterable of (category, amount_cents) pairs.
    """
    total = 0
    for category, amount_cents in lines:
        if not isinstance(amount_cents, int) or isinstance(amount_cents, bool):
            raise TypeError("amount_cents must be an int (cents), got %r" % (amount_cents,))
        if not is_exempt(category):
            total += amount_cents
    return total


def compute_tax(region, lines, discount_pct=0):
    """Return the sales tax in integer cents.

    Rules (data_tax/RULES.md):
      taxable = sum of taxable line amounts
      base    = taxable * (100 - discount_pct) / 100
      tax     = base * tax_pct / 100, rounded to the cent (half up)

    The discount is applied once to the taxable total, not per line.
    Intermediate values are exact (Decimal); only the final tax is rounded.
    """
    discount = Decimal(str(discount_pct))
    if discount < 0 or discount > _HUNDRED:
        raise ValueError("discount_pct must be between 0 and 100, got %r" % (discount_pct,))

    taxable = taxable_amount(lines)
    rate = tax_pct(region)  # raises KeyError for an unknown region

    base = Decimal(taxable) * (_HUNDRED - discount) / _HUNDRED
    tax = base * rate / _HUNDRED
    return int(tax.quantize(Decimal("1"), rounding=ROUND_HALF_UP))
