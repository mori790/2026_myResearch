"""Tax module. Owned by agent2. Computes sales tax.

The data files and rules are in data_tax/ next to this file:
  - rates.csv              : region -> tax percent (e.g. TX 8.25)
  - exempt_categories.csv  : item categories that are not taxed
  - RULES.md               : the tax rules

Agreed interface (decision log: tax.api v3, tax.unknown_customer v1,
PERCENT_REPRESENTATION v2, MONEY_REPRESENTATION v2):
  - money is integer cents (1250 means 12.50 dollars)
  - percents are percent numbers (10 means 10%, 8.25 means 8.25%)
  - region None means unknown customer: 0% tax, 0% discount
  - a region string that is not in rates.csv raises KeyError
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
            # Keep the exact decimal text from the file (no binary float rounding).
            rates[region] = Decimal(row["tax_pct"].strip())
    return rates


def _load_exempt(path):
    with open(path, newline="", encoding="utf-8") as f:
        return {row["category"].strip() for row in csv.DictReader(f) if row["category"].strip()}


_RATES = _load_rates(os.path.join(_DATA_DIR, "rates.csv"))
_EXEMPT = _load_exempt(os.path.join(_DATA_DIR, "exempt_categories.csv"))


def _check_discount(discount_pct):
    if isinstance(discount_pct, bool) or not isinstance(discount_pct, (int, float, Decimal)):
        raise TypeError("discount_pct must be a number (percent), got %r" % (discount_pct,))
    if not 0 <= discount_pct <= 100:
        raise ValueError("discount_pct must be between 0 and 100, got %r" % (discount_pct,))
    return Decimal(str(discount_pct))


def _tax_percent(region):
    """Return the tax percent (Decimal) for a region, 0 for an unknown customer (None).

    Raises KeyError for a region string that is not in rates.csv.
    """
    if region is None:
        return Decimal(0)
    return _RATES[region]


def tax_rate(region):
    """Return the sales tax percent for display, e.g. 8.25 for TX.

    Returns 0 when region is None (unknown customer).
    Raises KeyError for a region that is not in rates.csv.
    """
    return float(_tax_percent(region))


def compute_tax_cents(lines, region, discount_pct):
    """Return the sales tax for an order, in integer cents.

    lines        : iterable of dicts {"category": str, "amount_cents": int}
                   (line totals before discount, in integer cents)
    region       : customer region code such as "TX", or None for an unknown customer
    discount_pct : customer discount as a percent number (10 means 10%); 0 for none

    Rules (data_tax/RULES.md):
      taxable = sum of amount_cents of lines whose category is not exempt
      base    = taxable * (100 - discount_pct) / 100   (discount only on taxable lines)
      tax     = base * tax_pct / 100, rounded half up to the cent
    Unknown categories are treated as taxable.
    """
    discount = _check_discount(discount_pct)
    rate = _tax_percent(region)

    taxable = 0
    for line in lines:
        amount = line["amount_cents"]
        if isinstance(amount, bool) or not isinstance(amount, int):
            raise TypeError("amount_cents must be an int (cents), got %r" % (amount,))
        if line["category"].strip() not in _EXEMPT:
            taxable += amount

    base = Decimal(taxable) * (Decimal(100) - discount) / Decimal(100)
    tax = base * rate / Decimal(100)
    return int(tax.quantize(Decimal(1), rounding=ROUND_HALF_UP))
