"""Tax module. Owned by agent2. Computes sales tax.

The data files and rules are in data_tax/ next to this file:
  - data_tax/rates.csv                : region -> tax percent (e.g. TX,8.25)
  - data_tax/exempt_categories.csv    : categories that are not taxed
  - data_tax/RULES.md                 : the tax rules

Agreed interface (TAX_API v2 in the shared decision log):
  - Money crosses module boundaries as float dollars (pricing.money).
  - Discounts are fractions, 0.10 means 10% (pricing.percent).
  - Tax percentages are percent numbers, 8.25 means 8.25% (internal to this module).
  - tax_percent(region) returns None when the region is not in rates.csv (pricing.miss).
  - compute_tax(...) takes UNDISCOUNTED line amounts. The customer discount is applied
    here, to the taxable base only, so callers must not discount the lines first.
"""

import csv
import os
from decimal import Decimal, ROUND_HALF_UP

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_tax")
_CENT = Decimal("0.01")


def _load_rates():
    rates = {}
    with open(os.path.join(_DATA_DIR, "rates.csv"), newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            rates[row["region"].strip()] = Decimal(row["tax_pct"].strip())
    return rates


def _load_exempt_categories():
    exempt = set()
    with open(os.path.join(_DATA_DIR, "exempt_categories.csv"), newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            category = row["category"].strip()
            if category:
                exempt.add(category)
    return exempt


_RATES = _load_rates()              # region -> Decimal percent, e.g. Decimal("8.25")
_EXEMPT = _load_exempt_categories()  # set of exempt category strings


def tax_percent(region):
    """Return the tax percent (e.g. 8.25 for 8.25%) for a region.

    region None means the customer is unknown, and such a customer pays 0%.
    Returns None if the region is not in rates.csv (pricing.miss convention).
    """
    if region is None:
        return 0.0
    rate = _RATES.get(region)
    if rate is None:
        return None
    return float(rate)


def is_exempt(category):
    """True if the category is listed in exempt_categories.csv (exact match)."""
    return category in _EXEMPT


def compute_tax(lines, region, discount):
    """Compute sales tax for one order and return it as float dollars, rounded half-up to the cent.

    lines    : iterable of (amount, category). amount is a float in dollars, the undiscounted
               extended line amount (qty * unit_price). category is a str.
    region   : the customer's region string, or None for an unknown customer (tax is 0).
    discount : the customer's discount as a fraction (0.10 means 10% off), or 0 for none.

    Rules (data_tax/RULES.md):
      taxable_amount = sum of amounts of lines whose category is NOT exempt
      base           = taxable_amount * (1 - discount)
      tax            = base * tax_pct / 100, rounded half-up to the cent

    Raises ValueError if region is a non-None string that is not in rates.csv.
    """
    if region is None:
        return 0.0
    rate = _RATES.get(region)
    if rate is None:
        raise ValueError("unknown tax region: %r" % (region,))

    taxable = Decimal("0")
    for amount, category in lines:
        if not is_exempt(category):
            # Decimal(str(float)) keeps the decimal digits the caller wrote, so
            # float dollars such as 0.1 are not turned into binary noise.
            taxable += Decimal(str(amount))

    fraction = Decimal(str(discount))
    base = taxable * (Decimal("1") - fraction)
    tax = base * rate / Decimal("100")
    return float(tax.quantize(_CENT, rounding=ROUND_HALF_UP))
