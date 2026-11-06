"""Tax module. Owned by agent2. Computes sales tax. The data files and rules are in data_tax/ next to this file.

Public API (see agreement topic 'tax_api'):

    compute_tax(lines, region, discount_pct=0) -> int   (tax in integer cents)
    rate_pct(region) -> Decimal                          (tax percent for a region)
    is_exempt(category) -> bool

Conventions: money is integer cents, percentages are percent numbers (8.25 means 8.25%).
A lookup that finds nothing raises KeyError, except that an unknown customer
(region None) pays 0% tax, as stated in data_tax/RULES.md.
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
    exempt = set()
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            category = row["category"].strip()
            if category:
                exempt.add(category)
    return exempt


_RATES = _load_rates(os.path.join(_DATA_DIR, "rates.csv"))
_EXEMPT = _load_exempt(os.path.join(_DATA_DIR, "exempt_categories.csv"))


def rate_pct(region):
    """Return the sales tax percent for a customer region.

    region None means an unknown customer, which pays 0%.
    A region that is not in rates.csv raises KeyError.
    """
    if region is None:
        return Decimal("0")
    return _RATES[region]


def is_exempt(category):
    """Return True if items of this category are not taxed."""
    return category in _EXEMPT


def compute_tax(lines, region, discount_pct=0):
    """Compute sales tax for an order, in integer cents.

    lines        -- iterable of (category, amount_cents) for all order lines.
                    Lines whose category is exempt are not taxed.
    region       -- customer region (e.g. "TX"); None means unknown customer -> 0.
    discount_pct -- customer discount in percent (e.g. 10 for 10%).

    Rule (RULES.md):
        taxable   = sum of amounts of non-exempt lines
        base      = taxable * (100 - discount_pct) / 100
        tax       = base * tax_pct / 100, rounded to the cent (half up)
    """
    discount = Decimal(str(discount_pct))
    if not (Decimal("0") <= discount <= Decimal("100")):
        raise ValueError("discount_pct must be between 0 and 100, got %r" % (discount_pct,))

    taxable = 0
    for category, amount_cents in lines:
        if not is_exempt(category):
            taxable += int(amount_cents)

    rate = rate_pct(region)  # raises KeyError for an unknown region string

    # Use Decimal throughout to avoid binary floating-point error.
    # tax = taxable * (100 - discount) / 100 * rate / 100
    #     = taxable * (100 - discount) * rate / 10000
    tax = (Decimal(taxable) * (Decimal("100") - discount) * rate) / Decimal("10000")
    return int(tax.quantize(Decimal("1"), rounding=ROUND_HALF_UP))
