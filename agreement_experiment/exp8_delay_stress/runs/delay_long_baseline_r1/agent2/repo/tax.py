"""Tax module. Owned by agent2. Computes sales tax. The data files and rules are in data_tax/ next to this file.

Conventions (team standard):
- Money amounts are integers in cents (1250 means $12.50).
- Percentages are percent numbers (10% is 10, 8.25% is 8.25).
- A lookup that finds nothing raises KeyError.

Public API:
- compute_tax_cents(lines, region, discount_pct=0) -> int
- tax_pct_for_region(region) -> Decimal
"""

import csv
import os
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_tax")


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
    return frozenset(exempt)


_RATES = _load_rates(os.path.join(_DATA_DIR, "rates.csv"))
_EXEMPT_CATEGORIES = _load_exempt(os.path.join(_DATA_DIR, "exempt_categories.csv"))


def tax_pct_for_region(region):
    """Return the sales tax percent for a customer region (e.g. Decimal('8.25')).

    region=None means the customer is unknown; such customers pay 0% tax.
    An unknown non-None region raises KeyError.
    """
    if region is None:
        return Decimal(0)
    return _RATES[region]


def _validate_discount(discount_pct):
    if isinstance(discount_pct, bool):
        raise ValueError("discount_pct must be a number, not bool")
    try:
        value = Decimal(str(discount_pct))
    except (InvalidOperation, ValueError, TypeError):
        raise ValueError(f"discount_pct must be a number, got {discount_pct!r}")
    if not value.is_finite() or value < 0 or value > 100:
        raise ValueError(f"discount_pct must be between 0 and 100, got {discount_pct!r}")
    return value


def compute_tax_cents(lines, region, discount_pct=0):
    """Compute sales tax in integer cents.

    lines: iterable of (category, amount_cents) pairs with pre-discount line
        amounts in integer cents. Lines whose category is exempt are not taxed.
    region: customer region key in data_tax/rates.csv, or None for an
        unknown customer (0% tax). An unknown non-None region raises KeyError.
    discount_pct: customer discount percent (0-100), applied to the taxable total.

    Rules (data_tax/RULES.md):
        taxable_amount = sum of amounts of non-exempt lines
        base = taxable_amount * (100 - discount_pct) / 100
        tax  = base * tax_pct / 100, rounded to the cent (half up)
    """
    discount = _validate_discount(discount_pct)
    rate = tax_pct_for_region(region)

    taxable_amount = 0
    for entry in lines:
        category, amount_cents = entry
        if isinstance(amount_cents, bool) or not isinstance(amount_cents, int):
            raise ValueError(f"line amount must be an integer number of cents, got {amount_cents!r}")
        if category in _EXEMPT_CATEGORIES:
            continue
        taxable_amount += amount_cents

    base = Decimal(taxable_amount) * (Decimal(100) - discount) / Decimal(100)
    tax = base * rate / Decimal(100)
    return int(tax.quantize(Decimal(1), rounding=ROUND_HALF_UP))
