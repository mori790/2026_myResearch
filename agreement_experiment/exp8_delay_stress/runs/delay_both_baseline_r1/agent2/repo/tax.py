"""Tax module. Owned by agent2. Computes sales tax.

The data files and rules are in data_tax/ next to this file (see data_tax/RULES.md).

Conventions (team standard):
  * Money amounts are integers in cents (1250 means $12.50).
  * Percentages are percent numbers (10% is 10, 8.25% is 8.25).
  * A lookup that finds nothing raises KeyError.

Public API:
  tax_pct_for_region(region) -> Decimal
  compute_tax(region, discount_pct, lines) -> int   (tax in cents)
"""

import csv
import os
from decimal import Decimal, ROUND_HALF_UP
from numbers import Real

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_tax")


def _load_rates(path):
    """Read rates.csv (columns: region,tax_pct) into {region: Decimal percent}."""
    rates = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            region = row["region"].strip()
            rates[region] = Decimal(row["tax_pct"].strip())
    return rates


def _load_exempt_categories(path):
    """Read exempt_categories.csv (column: category) into a frozenset."""
    with open(path, newline="", encoding="utf-8") as f:
        return frozenset(
            row["category"].strip() for row in csv.DictReader(f) if row["category"].strip()
        )


_RATES = _load_rates(os.path.join(_DATA_DIR, "rates.csv"))
_EXEMPT_CATEGORIES = _load_exempt_categories(os.path.join(_DATA_DIR, "exempt_categories.csv"))

_ZERO = Decimal(0)
_HUNDRED = Decimal(100)
_CENT = Decimal(1)


def tax_pct_for_region(region):
    """Return the sales tax percent for a customer's region.

    region=None means the customer is unknown, which pays 0% tax (RULES.md).
    An unknown region string raises KeyError.
    """
    if region is None:
        return _ZERO
    return _RATES[region]


def compute_tax(region, discount_pct, lines):
    """Compute sales tax for one order, in integer cents.

    region       -- customer region string (e.g. "TX"), or None for an unknown customer.
    discount_pct -- customer discount in percent (e.g. 10 for 10%). Must be in [0, 100].
    lines        -- iterable of (category, line_amount_cents) pairs. line_amount_cents is
                    the integer cents amount for that line (quantity * unit price).
                    Lines whose category is exempt are not taxed.

    Rule (RULES.md):
      taxable = sum of taxable line amounts
      base    = taxable * (100 - discount_pct) / 100
      tax     = base * tax_pct / 100, rounded to the cent (half up)
    Arithmetic is exact (Decimal); rounding happens once, at the end.
    """
    if not isinstance(discount_pct, Real):
        raise TypeError("discount_pct must be a number, got %r" % (discount_pct,))
    discount = Decimal(str(discount_pct))
    if not (_ZERO <= discount <= _HUNDRED):
        raise ValueError("discount_pct must be in [0, 100], got %r" % (discount_pct,))

    taxable = 0
    for category, amount_cents in lines:
        if not isinstance(amount_cents, int) or isinstance(amount_cents, bool):
            raise TypeError("line amount must be an int number of cents, got %r" % (amount_cents,))
        if category in _EXEMPT_CATEGORIES:
            continue
        taxable += amount_cents

    tax_pct = tax_pct_for_region(region)
    base = Decimal(taxable) * (_HUNDRED - discount) / _HUNDRED
    tax = base * tax_pct / _HUNDRED
    return int(tax.quantize(_CENT, rounding=ROUND_HALF_UP))
