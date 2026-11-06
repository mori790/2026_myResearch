"""Tax module. Owned by agent2. Computes sales tax.

The data files and rules are in data_tax/ next to this file:
  - rates.csv              region -> tax percent (e.g. TX = 8.25)
  - exempt_categories.csv  item categories that are not taxed (e.g. food)
  - RULES.md               the tax rules

Team conventions (committed decisions tax_interface, tax_rate, pricing_api):
  - Money is an integer number of cents (1250 means $12.50).
  - Percentages are percent numbers (10 means 10%, 8.25 means 8.25%).
  - A lookup that finds nothing raises KeyError, except that a None region
    (unknown customer) pays 0% tax.
"""

import csv
import os
from decimal import Decimal, ROUND_HALF_UP

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_tax")


def _load_rates(path):
    """Return {region: Decimal percent} from rates.csv."""
    rates = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            region = row["region"].strip()
            rates[region] = Decimal(row["tax_pct"].strip())
    return rates


def _load_exempt(path):
    """Return the set of exempt item categories from exempt_categories.csv."""
    with open(path, newline="", encoding="utf-8") as f:
        return {row["category"].strip() for row in csv.DictReader(f)
                if row["category"].strip()}


_RATES = _load_rates(os.path.join(_DATA_DIR, "rates.csv"))
_EXEMPT_CATEGORIES = _load_exempt(os.path.join(_DATA_DIR, "exempt_categories.csv"))


def _rate_for(region):
    """Return the tax percent as a Decimal. None -> 0 (unknown customer).

    Raises KeyError if region is a non-null string that is not in rates.csv.
    """
    if region is None:
        return Decimal(0)
    return _RATES[region]


def rate_percent(region):
    """Return the tax rate for a region as a percent number.

    Returns an int when the rate is whole (e.g. 0 for OR, 0 for None) and a
    float otherwise (e.g. 8.25 for TX). Raises KeyError for an unknown region.
    """
    rate = _rate_for(region)
    if rate == rate.to_integral_value():
        return int(rate)
    return float(rate)


def compute_tax(region, lines, discount_pct):
    """Return the sales tax for an invoice, in integer cents.

    region        : customer region code such as "TX", or None for an unknown
                    customer (tax 0). A non-null region not in rates.csv raises
                    KeyError.
    lines         : list of dicts {"category": str, "amount_cents": int}, one per
                    invoice line. Lines whose category is in
                    exempt_categories.csv are excluded from the taxable base.
    discount_pct  : customer discount as a percent number (10 means 10%), 0 if
                    none. It is applied to the taxable amount.

    Rule (RULES.md):
      taxable    = sum of taxable line amounts (cents)
      base       = taxable * (100 - discount_pct) / 100
      tax        = base * tax_pct / 100, rounded to the cent (half up)
    """
    rate = _rate_for(region)

    taxable_cents = sum(
        int(line["amount_cents"])
        for line in lines
        if line["category"] not in _EXEMPT_CATEGORIES
    )

    # Decimal(str(...)) keeps values such as 8.25 and 10 exact (no float error).
    discount = Decimal(str(discount_pct))
    base = Decimal(taxable_cents) * (Decimal(100) - discount) / Decimal(100)

    tax = base * rate / Decimal(100)
    return int(tax.quantize(Decimal(1), rounding=ROUND_HALF_UP))
