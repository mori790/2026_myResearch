"""Tax module. Owned by agent2. Computes sales tax. The data files and rules are in data_tax/ next to this file.

Conventions (team standard):
- Money amounts are integers in cents (1250 means $12.50).
- Percentages are percent numbers (10% is 10, 8.25% is 8.25).
- A lookup that finds nothing raises KeyError.

Public API:
- calculate_tax(lines, region, discount_pct=0) -> int (cents)
- tax_rate_pct(region) -> Decimal (percent)
- is_exempt(category) -> bool

Rules (see data_tax/RULES.md):
- Tax percent depends on the customer's region (rates.csv).
- Items whose category is in exempt_categories.csv are not taxed.
- base = taxable_amount * (100 - discount_pct) / 100
- tax = base * tax_pct / 100, rounded to the cent (half up), rounded once at the end.
- An unknown customer (region None) pays 0% tax.
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
            if region:
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
_EXEMPT = _load_exempt(_EXEMPT_PATH)


def tax_rate_pct(region):
    """Return the tax percent (Decimal, e.g. Decimal('8.25')) for a customer region.

    region=None means an unknown customer, which pays 0%.
    An unknown region raises KeyError.
    """
    if region is None:
        return Decimal("0")
    return _RATES[region]


def is_exempt(category):
    """True if items in this category are not taxed."""
    return category in _EXEMPT


def calculate_tax(lines, region, discount_pct=0):
    """Return the sales tax in cents for one order.

    lines: iterable of (category, amount_cents) pairs; amount_cents is an int.
    region: customer region code (e.g. "TX"), or None for an unknown customer.
    discount_pct: customer discount percent (e.g. 10 for 10%).

    Only lines whose category is not exempt count toward the taxable amount.
    All arithmetic uses Decimal; the result is rounded half up once, at the end.
    """
    taxable = 0
    for category, amount_cents in lines:
        if isinstance(amount_cents, bool) or not isinstance(amount_cents, int):
            raise TypeError("amount_cents must be an int (cents), got %r" % (amount_cents,))
        if not is_exempt(category):
            taxable += amount_cents

    rate = tax_rate_pct(region)
    discount = Decimal(str(discount_pct))

    base = Decimal(taxable) * (Decimal(100) - discount) / Decimal(100)
    tax = base * rate / Decimal(100)
    return int(tax.quantize(Decimal("1"), rounding=ROUND_HALF_UP))
