"""Tax module. Owned by agent2. Computes sales tax.

The data files and rules are in data_tax/ next to this file.

Conventions (team standard):
  * Money amounts are integers in cents (1250 == $12.50).
  * Percentages are percent numbers (10 == 10%, 8.25 == 8.25%).
  * A lookup that finds nothing raises KeyError.

Exception to the lookup rule (from data_tax/RULES.md): an unknown customer
pays 0% tax. The caller signals an unknown customer by passing region=None;
that yields 0%. A region string that is not in rates.csv raises KeyError.

Public API:
  tax_pct_for_region(region) -> Decimal
  is_exempt(category) -> bool
  taxable_amount_cents(lines) -> int
  sales_tax_cents(region, lines, discount_pct=0) -> int
"""

import csv
import os
from decimal import Decimal, ROUND_HALF_UP

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_tax")
_RATES_PATH = os.path.join(_DATA_DIR, "rates.csv")
_EXEMPT_PATH = os.path.join(_DATA_DIR, "exempt_categories.csv")


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
            category = (row.get("category") or "").strip().casefold()
            if category:
                exempt.add(category)
    return exempt


_RATES = _load_rates()
_EXEMPT = _load_exempt()


def tax_pct_for_region(region):
    """Return the tax percent (Decimal) for a region code, e.g. 'TX' -> 8.25.

    region=None means the customer is unknown; such customers pay 0%.
    An unknown region code raises KeyError.
    """
    if region is None:
        return Decimal("0")
    return _RATES[region]


def is_exempt(category):
    """True if items in this category are not taxed."""
    return str(category).strip().casefold() in _EXEMPT


def taxable_amount_cents(lines):
    """Sum of line amounts (cents) whose category is not exempt.

    lines: iterable of (category, amount_cents) pairs.
    """
    total = 0
    for category, amount_cents in lines:
        if not isinstance(amount_cents, int):
            raise TypeError("amount_cents must be an int (cents), got %r" % (amount_cents,))
        if not is_exempt(category):
            total += amount_cents
    return total


def sales_tax_cents(region, lines, discount_pct=0):
    """Compute sales tax in integer cents.

    Rule (data_tax/RULES.md):
      taxable = sum of non-exempt line amounts
      base    = taxable * (100 - discount_pct) / 100
      tax     = base * tax_pct / 100, rounded to the cent (half up)

    region       : region code from rates.csv, or None for an unknown customer (0%).
    lines        : iterable of (category, amount_cents) pairs.
    discount_pct : customer discount as a percent number (0..100).
    """
    discount = Decimal(str(discount_pct))
    if discount < 0 or discount > 100:
        raise ValueError("discount_pct must be between 0 and 100, got %r" % (discount_pct,))

    taxable = Decimal(taxable_amount_cents(lines))
    base = taxable * (Decimal(100) - discount) / Decimal(100)
    tax = base * tax_pct_for_region(region) / Decimal(100)
    return int(tax.quantize(Decimal("1"), rounding=ROUND_HALF_UP))
