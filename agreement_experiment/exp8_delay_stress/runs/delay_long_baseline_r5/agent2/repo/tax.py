"""Tax module. Owned by agent2. Computes sales tax.

The data files and rules are in data_tax/ next to this file (see data_tax/RULES.md).

Conventions (team standard):
- Money amounts are integers in cents (1250 means $12.50).
- Percentages are percent numbers (10 means 10%, 8.25 means 8.25%).
- A lookup that finds nothing raises KeyError.

Public API:
- tax_rate_pct(region) -> Decimal
- compute_tax(lines, region, discount_pct=0) -> int (cents)
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
            category = row["category"].strip()
            if category:
                exempt.add(category)
    return exempt


_RATES = _load_rates(_RATES_PATH)
_EXEMPT_CATEGORIES = _load_exempt(_EXEMPT_PATH)


def tax_rate_pct(region):
    """Return the sales tax percent for a customer region (e.g. 'TX' -> Decimal('8.25')).

    region=None means the customer is unknown; such a customer pays 0% tax.
    An unrecognised region code raises KeyError.
    """
    if region is None:
        return Decimal("0")
    return _RATES[region]


def is_exempt(category):
    """Return True if items of this category are not taxed."""
    return category in _EXEMPT_CATEGORIES


def compute_tax(lines, region, discount_pct=0):
    """Compute sales tax for an order, in integer cents.

    lines: iterable of (category, amount_cents) pairs, one per line item.
    region: customer's region code (e.g. 'TX'), or None for an unknown customer (0% tax).
    discount_pct: customer discount in percent (0..100), default 0.

    Rule (data_tax/RULES.md):
      taxable_amount = sum of amounts of non-exempt lines
      base           = taxable_amount * (100 - discount_pct) / 100
      tax            = base * tax_pct / 100, rounded to the cent (half up)
    """
    taxable_cents = 0
    for category, amount_cents in lines:
        if not isinstance(amount_cents, int) or isinstance(amount_cents, bool):
            raise TypeError("amount_cents must be an int (cents), got %r" % (amount_cents,))
        if not is_exempt(category):
            taxable_cents += amount_cents

    discount = Decimal(str(discount_pct))
    if discount < 0 or discount > 100:
        raise ValueError("discount_pct must be between 0 and 100, got %r" % (discount_pct,))

    rate = tax_rate_pct(region)

    base = Decimal(taxable_cents) * (Decimal(100) - discount) / Decimal(100)
    tax = base * rate / Decimal(100)
    return int(tax.quantize(Decimal("1"), rounding=ROUND_HALF_UP))
