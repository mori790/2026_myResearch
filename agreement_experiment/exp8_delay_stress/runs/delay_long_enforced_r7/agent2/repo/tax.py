"""Tax module. Owned by agent2. Computes sales tax.

The data files and rules are in data_tax/ next to this file.

Team decisions this module follows (committed in the agreement log):
  - money_percent_repr v1: money is integer cents (1250 = $12.50);
    percents are percent numbers (10 = 10%, 8.25 = 8.25%).
    Tax is rounded once to the cent, half up.
  - tax_api v1: compute_order_tax(lines, region, discount_pct) -> int cents;
    tax_rate_pct(region); is_exempt(category) -> bool.
  - unknown_customer v2: region=None (unknown customer) -> 0 tax.
    A region string that is not in rates.csv raises KeyError.

Tax rules (data_tax/RULES.md):
  base = taxable_amount * (100 - discount_pct) / 100
  tax  = base * tax_pct / 100, rounded to the cent (half up)
  Items whose category is listed in exempt_categories.csv are not taxed.
"""

import csv
import os
from decimal import Decimal, ROUND_HALF_UP

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_tax")
_RATES_PATH = os.path.join(_DATA_DIR, "rates.csv")
_EXEMPT_PATH = os.path.join(_DATA_DIR, "exempt_categories.csv")


def _load_rates(path):
    """Return {region: tax_pct as Decimal} read from rates.csv."""
    rates = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            region = row["region"].strip()
            rates[region] = Decimal(row["tax_pct"].strip())
    return rates


def _load_exempt(path):
    """Return the set of exempt category names read from exempt_categories.csv."""
    with open(path, newline="", encoding="utf-8") as f:
        return {row["category"].strip() for row in csv.DictReader(f) if row["category"].strip()}


_RATES = _load_rates(_RATES_PATH)
_EXEMPT = _load_exempt(_EXEMPT_PATH)


def tax_rate_pct(region):
    """Return the sales tax rate (percent number, e.g. Decimal('8.25')) for a region.

    Raises KeyError if the region is not listed in rates.csv.
    """
    if region not in _RATES:
        raise KeyError(f"no tax rate for region {region!r}")
    return _RATES[region]


def is_exempt(category):
    """Return True if items in this category are not taxed (exempt_categories.csv)."""
    return category in _EXEMPT


def compute_order_tax(lines, region, discount_pct):
    """Return the total sales tax for an order, in integer cents.

    lines: iterable of (category, amount_cents) pairs, one per line item.
           amount_cents is an int (1250 = $12.50).
    region: the customer's region string (e.g. "TX"), or None for an
            unknown customer, which pays 0 tax.
    discount_pct: the customer's discount as a percent number (10 = 10% off);
                  0 or None means no discount.

    Raises KeyError if region is a string that is not in rates.csv.
    """
    if region is None:
        return 0

    tax_pct = tax_rate_pct(region)

    taxable_cents = 0
    for category, amount_cents in lines:
        if not isinstance(amount_cents, int) or isinstance(amount_cents, bool):
            raise TypeError(f"amount_cents must be int, got {amount_cents!r}")
        if not is_exempt(category):
            taxable_cents += amount_cents

    if discount_pct is None:
        discount_pct = 0
    discount = Decimal(str(discount_pct))

    # Exact value in cents:
    #   base = taxable * (100 - discount) / 100
    #   tax  = base * tax_pct / 100
    # so tax_cents = taxable * (100 - discount) * tax_pct / 10000.
    # Decimal keeps the arithmetic exact enough; we round once at the end.
    exact_tax_cents = (
        Decimal(taxable_cents) * (Decimal(100) - discount) * tax_pct / Decimal(10000)
    )
    return int(exact_tax_cents.quantize(Decimal("1"), rounding=ROUND_HALF_UP))
