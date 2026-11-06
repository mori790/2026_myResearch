"""Tax module. Owned by agent2. Computes sales tax.

The data files and rules are in data_tax/ next to this file.

Conventions (team standard):
- Money amounts are integers in cents (1250 means $12.50).
- Percentages are percent numbers (10% is 10, 8.25% is 8.25).
- A lookup that finds nothing raises KeyError.

Public API:
- compute_tax(lines, region, discount_pct=0) -> int (tax in cents)
- tax_rate_pct(region) -> Decimal (percent)
- is_exempt(category) -> bool
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
_EXEMPT = _load_exempt(_EXEMPT_PATH)


def tax_rate_pct(region):
    """Return the sales tax percent for a customer region, as a Decimal.

    region=None means the customer is unknown, which pays 0% tax.
    Raises KeyError if the region is not listed in rates.csv.
    """
    if region is None:
        return Decimal("0")
    return _RATES[region]


def is_exempt(category):
    """Return True if items of this category are not taxed (exempt_categories.csv)."""
    return category in _EXEMPT


def compute_tax(lines, region, discount_pct=0):
    """Compute sales tax for an order and return it in integer cents.

    lines: iterable of (category, amount_cents) for every line in the order.
           Lines whose category is exempt are ignored.
    region: customer region code (e.g. "TX"), or None for an unknown customer
            (tax is 0).
    discount_pct: customer discount in percent (10 means 10%). Default 0.

    Rules (RULES.md):
        taxable   = sum of amounts of non-exempt lines (cents)
        base      = taxable * (100 - discount_pct) / 100
        tax       = base * tax_pct / 100, rounded to the cent (half up)

    Raises KeyError if region is not None and not in rates.csv.
    Raises ValueError if discount_pct is outside 0..100.
    """
    discount = Decimal(str(discount_pct))
    if discount < 0 or discount > 100:
        raise ValueError(f"discount_pct must be between 0 and 100, got {discount_pct!r}")

    taxable_cents = 0
    for category, amount_cents in lines:
        if not is_exempt(category):
            taxable_cents += int(amount_cents)

    rate = tax_rate_pct(region)

    base = Decimal(taxable_cents) * (Decimal(100) - discount) / Decimal(100)
    tax = base * rate / Decimal(100)
    return int(tax.quantize(Decimal("1"), rounding=ROUND_HALF_UP))
