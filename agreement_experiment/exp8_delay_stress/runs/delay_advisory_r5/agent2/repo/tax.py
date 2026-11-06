"""Tax module. Owned by agent2. Computes sales tax.

The data files and rules are in data_tax/ next to this file:
  - rates.csv               : region -> tax percent (e.g. TX 8.25)
  - exempt_categories.csv   : item categories that are not taxed
  - RULES.md                : the tax rules (see compute_tax below)

Team conventions (decision log: TAX_API, TAX_UNKNOWN):
  - Money amounts are integers in cents (1250 means $12.50).
  - Percentages are percent numbers (10 means 10%, 8.25 means 8.25%).
  - A lookup that finds nothing raises KeyError, except that region=None
    means an unknown customer, who pays 0% tax.

Public API:
  compute_tax(lines, region, discount_pct) -> int cents
  tax_percent(region) -> number (percent)
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
    """Return the set of exempt category names from exempt_categories.csv."""
    exempt = set()
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            category = row["category"].strip()
            if category:
                exempt.add(category)
    return exempt


_RATES = _load_rates(os.path.join(_DATA_DIR, "rates.csv"))
_EXEMPT = _load_exempt(os.path.join(_DATA_DIR, "exempt_categories.csv"))


def _check_cents(value, name):
    # bool is a subclass of int, so exclude it explicitly.
    if not isinstance(value, int) or isinstance(value, bool):
        raise TypeError(f"{name} must be an int number of cents, got {value!r}")


def tax_percent(region):
    """Return the tax percent for a region (e.g. 8.25 for TX).

    region=None (unknown customer) gives 0. A non-None region that is not in
    rates.csv raises KeyError.
    """
    if region is None:
        return 0
    try:
        rate = _RATES[region]
    except KeyError:
        raise KeyError(f"unknown tax region: {region!r}") from None
    return float(rate)


def compute_tax(lines, region, discount_pct):
    """Return the sales tax for an order, as an int number of cents.

    lines: iterable of (category, amount_cents) pairs, one per order line.
           Lines whose category is exempt are not taxed.
    region: customer region code (e.g. "TX"), or None for an unknown
            customer (tax is 0).
    discount_pct: customer discount as a percent number (10 means 10% off),
                  0 if none.

    Rule (data_tax/RULES.md):
      taxable  = sum of amounts of non-exempt lines
      base     = taxable * (100 - discount_pct) / 100
      tax      = base * tax_pct / 100, rounded to the cent (half up)
    """
    taxable = 0
    for category, amount_cents in lines:
        _check_cents(amount_cents, "line amount")
        if category not in _EXEMPT:
            taxable += amount_cents

    if region is None:
        return 0

    try:
        rate = _RATES[region]
    except KeyError:
        raise KeyError(f"unknown tax region: {region!r}") from None

    discount = Decimal(discount_pct)
    if discount < 0 or discount > 100:
        raise ValueError(f"discount_pct must be between 0 and 100, got {discount_pct!r}")

    # Exact arithmetic on Decimal; round only once, at the end.
    tax = Decimal(taxable) * (Decimal(100) - discount) * rate / Decimal(10000)
    return int(tax.quantize(Decimal(1), rounding=ROUND_HALF_UP))
