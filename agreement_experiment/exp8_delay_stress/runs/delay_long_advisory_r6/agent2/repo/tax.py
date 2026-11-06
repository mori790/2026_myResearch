"""Tax module. Owned by agent2. Computes sales tax.

The data files and rules are in data_tax/ next to this file:
  - rates.csv               region -> tax percent (e.g. TX -> 8.25)
  - exempt_categories.csv   item categories that are not taxed
  - RULES.md                the tax rules this module implements

Interface (committed as decision tax_api_v2 in the shared log):
  tax_rate(region)                    -> float fraction (0.0825 for TX)
  tax_amount(region, lines, discount) -> float dollars, rounded half up to the cent

Conventions (team standard): money is float dollars at the boundary,
percentages are fractions at the boundary (0.10 means 10 percent),
an unknown customer is signalled by region None.
Internally all arithmetic is exact, using Decimal.
"""

import csv
import os
from decimal import Decimal, ROUND_HALF_UP

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_tax")
_CENT = Decimal("0.01")
_HUNDRED = Decimal("100")


def _load_rates(path):
    rates = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            region = row["region"].strip()
            rates[region] = Decimal(row["tax_pct"].strip())  # percent number, e.g. 8.25
    return rates


def _load_exempt(path):
    exempt = set()
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            category = row["category"].strip()
            if category:
                exempt.add(category)
    return exempt


_RATES_PCT = _load_rates(os.path.join(_DATA_DIR, "rates.csv"))
_EXEMPT_CATEGORIES = _load_exempt(os.path.join(_DATA_DIR, "exempt_categories.csv"))


def _rate_decimal(region):
    """Return the tax rate as an exact Decimal fraction. Unknown customer (None) pays 0%.

    Raises KeyError for a region string that is not in rates.csv.
    """
    if region is None:
        return Decimal("0")
    return _RATES_PCT[region] / _HUNDRED


def tax_rate(region):
    """Tax rate as a fraction: 0.0825 for TX, 0.0 for OR or for region None."""
    return float(_rate_decimal(region))


def tax_amount(region, lines, discount):
    """Sales tax in dollars for one order.

    region   : customer region code (e.g. "TX"), or None for an unknown customer.
    lines    : iterable of (category, amount) pairs; amount is the line total in
               float dollars before discount.
    discount : customer discount as a fraction (0.10 means 10 percent off, 0 for none).

    Rule (data_tax/RULES.md):
      taxable = sum of line amounts whose category is not exempt
      base    = taxable * (1 - discount)
      tax     = base * rate, rounded half up to the cent
    """
    rate = _rate_decimal(region)
    taxable = Decimal("0")
    for category, amount in lines:
        if category in _EXEMPT_CATEGORIES:
            continue
        taxable += Decimal(str(amount))
    base = taxable * (Decimal("1") - Decimal(str(discount)))
    tax = (base * rate).quantize(_CENT, rounding=ROUND_HALF_UP)
    return float(tax)
