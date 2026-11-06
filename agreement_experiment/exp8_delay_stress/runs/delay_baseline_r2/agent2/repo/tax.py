"""Tax module. Owned by agent2. Computes sales tax.

The data files and rules are in data_tax/ next to this file (see data_tax/RULES.md).

Public API
----------
compute_tax(lines, region, discount_pct=0) -> int
    Returns the sales tax for one invoice, in integer cents.

    lines        : iterable of (category: str, amount_cents: int) pairs, one per
                   invoice line. Lines whose category is listed in
                   exempt_categories.csv are not taxed.
    region       : customer region code, e.g. "TX" (must be in rates.csv).
                   Pass None for an unknown customer: the tax is 0.
    discount_pct : customer discount in percent (e.g. 10 means 10%), 0..100.

Errors
------
KeyError   : region is not None and is not listed in rates.csv.
ValueError : discount_pct is outside 0..100, or an amount is negative.

Rounding
--------
base = taxable_amount * (100 - discount_pct) / 100
tax  = base * tax_pct / 100, rounded to the nearest cent (half up).
The computation is done with Decimal and rounded once at the end, so no
intermediate rounding error is introduced.
"""

import csv
import os
from decimal import Decimal, ROUND_HALF_UP

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_tax")
_RATES_PATH = os.path.join(_DATA_DIR, "rates.csv")
_EXEMPT_PATH = os.path.join(_DATA_DIR, "exempt_categories.csv")


def _load_rates(path=_RATES_PATH):
    """Return {region: Decimal tax percent} from rates.csv."""
    rates = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            region = row["region"].strip()
            rates[region] = Decimal(row["tax_pct"].strip())
    return rates


def _load_exempt(path=_EXEMPT_PATH):
    """Return the set of exempt category names from exempt_categories.csv."""
    exempt = set()
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            category = row["category"].strip()
            if category:
                exempt.add(category)
    return exempt


_RATES = _load_rates()
_EXEMPT = _load_exempt()


def tax_percent(region):
    """Return the tax percent (Decimal) for a region. None means unknown customer -> 0.

    Raises KeyError if the region is not in rates.csv.
    """
    if region is None:
        return Decimal("0")
    return _RATES[region]


def is_exempt(category):
    """True if items of this category are not taxed."""
    return category in _EXEMPT


def compute_tax(lines, region, discount_pct=0):
    """Compute the sales tax for an invoice, in integer cents. See module docstring."""
    discount = Decimal(str(discount_pct))
    if discount < 0 or discount > 100:
        raise ValueError("discount_pct must be between 0 and 100, got %r" % (discount_pct,))

    rate = tax_percent(region)  # raises KeyError for an unknown region

    taxable_cents = 0
    for category, amount_cents in lines:
        if amount_cents < 0:
            raise ValueError("line amount must not be negative, got %r" % (amount_cents,))
        if not is_exempt(category):
            taxable_cents += int(amount_cents)

    # tax_cents = taxable * (100 - d)/100 * rate/100, computed exactly, rounded half up once.
    exact = Decimal(taxable_cents) * (Decimal(100) - discount) * rate / Decimal(10000)
    return int(exact.quantize(Decimal("1"), rounding=ROUND_HALF_UP))
