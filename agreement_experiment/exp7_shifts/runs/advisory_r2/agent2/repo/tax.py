"""Tax module. Owned by agent2. Computes sales tax. The data files and rules are in data_tax/ next to this file.

Conventions (committed in the shared decision log):
  - money: float dollars (12.5 means $12.50)
  - percent: fraction (0.10 means 10%)
  - a lookup that finds nothing returns None

Public API (committed as tax_api v1):
  compute_tax(lines, customer) -> float dollars, rounded to the cent (half up)
  get_tax_rate(region)         -> fraction float, or None if region is unknown
  is_exempt(category)          -> bool
"""

import csv
import os
from decimal import Decimal, ROUND_HALF_UP

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_tax")
_CENT = Decimal("0.01")


def _load_rates():
    """rates.csv stores percent numbers (8.25); keep them as exact fractions (0.0825)."""
    rates = {}
    path = os.path.join(_DATA_DIR, "rates.csv")
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            region = row["region"].strip()
            rates[region] = Decimal(row["tax_pct"].strip()) / Decimal(100)
    return rates


def _load_exempt_categories():
    path = os.path.join(_DATA_DIR, "exempt_categories.csv")
    categories = set()
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            name = row["category"].strip()
            if name:
                categories.add(name)
    return categories


_RATES = _load_rates()
_EXEMPT = _load_exempt_categories()


def _dec(value):
    """Convert a float/int dollar or fraction to Decimal using its shortest repr.

    This avoids binary float noise, e.g. 0.1 -> Decimal('0.1') rather than 0.1000000000000000055...
    """
    return Decimal(repr(float(value)))


def get_tax_rate(region):
    """Return the sales tax rate for a 2-letter region code as a fraction, or None if unknown."""
    rate = _RATES.get(region)
    if rate is None:
        return None
    return float(rate)


def is_exempt(category):
    """Return True if items in this category are not taxed (listed in exempt_categories.csv)."""
    return category in _EXEMPT


def compute_tax(lines, customer):
    """Compute the sales tax for an invoice.

    lines:    list of {"category": str, "amount": float dollars}
              where amount = unit price x quantity, before any discount.
    customer: dict from pricing.get_customer(id) ({"discount": fraction, "region": str}),
              or None for an unknown customer (which pays 0% tax).

    Rule (RULES.md):
      taxable = sum of amounts of non-exempt lines
      base    = taxable * (100 - discount_pct) / 100      (discount as fraction: taxable * (1 - discount))
      tax     = base * tax_pct / 100, rounded to the cent (half up), once on the invoice total

    Raises ValueError if the customer's region has no rate in rates.csv.
    """
    if customer is None:
        return 0.0

    region = customer["region"]
    rate = _RATES.get(region)
    if rate is None:
        raise ValueError(f"no tax rate for region {region!r} in rates.csv")

    taxable = Decimal(0)
    for line in lines:
        if is_exempt(line["category"]):
            continue
        taxable += _dec(line["amount"])

    discount = _dec(customer["discount"])
    base = taxable * (Decimal(1) - discount)
    tax = (base * rate).quantize(_CENT, rounding=ROUND_HALF_UP)
    return float(tax)
