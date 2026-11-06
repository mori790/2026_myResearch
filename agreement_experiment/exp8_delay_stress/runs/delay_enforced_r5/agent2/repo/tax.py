"""Tax module. Owned by agent2. Computes sales tax.

The data files and rules are in data_tax/ next to this file.

Agreed interface (decision topic 'tax_api' v2):
  compute_tax(region, lines, discount_pct) -> int   tax in integer cents
  rate_percent(region) -> float                     tax percent, display only

Conventions:
  - money: integer cents (1250 means $12.50)
  - percents: percent numbers (10 means 10%, 8.25 means 8.25%)
  - a non-null region not in rates.csv raises KeyError
  - region None (unknown customer) pays 0% tax (data_tax/RULES.md)
"""

import csv
import os
from fractions import Fraction
from math import floor

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_tax")


def _load_rates():
    """Map region code -> tax percent as an exact Fraction, from rates.csv."""
    rates = {}
    with open(os.path.join(_DATA_DIR, "rates.csv"), newline="") as f:
        for row in csv.DictReader(f):
            rates[row["region"].strip()] = Fraction(row["tax_pct"].strip())
    return rates


def _load_exempt_categories():
    """Set of item categories that are not taxed, from exempt_categories.csv."""
    exempt = set()
    with open(os.path.join(_DATA_DIR, "exempt_categories.csv"), newline="") as f:
        for row in csv.DictReader(f):
            exempt.add(row["category"].strip())
    return exempt


_RATES = _load_rates()
_EXEMPT = _load_exempt_categories()


def rate_percent(region):
    """Return the tax percent for a region (e.g. 8.25 for 8.25%).

    Display only: never use the returned float in money arithmetic.
    region None (unknown customer) -> 0. Unknown region -> KeyError.
    """
    if region is None:
        return 0
    return float(_RATES[region])


def compute_tax(region, lines, discount_pct):
    """Return the sales tax for an order, in integer cents.

    region       : customer region code (e.g. "TX"), or None for an unknown customer
    lines        : list of {"category": str, "amount_cents": int}; amount_cents is
                   the line total (unit price * qty) before discount and tax
    discount_pct : customer discount as a percent number (10 means 10%); 0 if none

    Rule (data_tax/RULES.md):
      taxable = sum of amount_cents for lines whose category is not exempt
      base    = taxable * (100 - discount_pct) / 100
      tax     = base * tax_pct / 100, rounded to the cent (half up)

    All arithmetic is exact (Fraction); rounding happens once, at the end.
    """
    if region is None:
        return 0

    rate = _RATES[region]  # KeyError for an unknown region

    discount = Fraction(str(discount_pct))
    if not 0 <= discount <= 100:
        raise ValueError(f"discount_pct must be between 0 and 100, got {discount_pct!r}")

    taxable = 0
    for line in lines:
        if line["category"].strip() in _EXEMPT:
            continue
        taxable += int(line["amount_cents"])

    base = Fraction(taxable) * (100 - discount) / 100
    tax = base * rate / 100

    # Round half up to the nearest cent. tax is never negative here.
    return int(floor(tax + Fraction(1, 2)))
