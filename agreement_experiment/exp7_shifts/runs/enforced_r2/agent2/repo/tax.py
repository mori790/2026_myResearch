"""Tax module. Owned by agent2. Computes sales tax.

The data files and rules are in data_tax/ next to this file:
  - data_tax/rates.csv              region -> tax_pct (percent number, e.g. 8.25)
  - data_tax/exempt_categories.csv  item categories that are not taxed
  - data_tax/RULES.md               the tax rules (see compute_tax)

Public API (see the committed decision `tax_api`):
  get_rate(region)                       -> float   tax percent for a region; KeyError if unknown
  is_exempt(category)                    -> bool    True if the category is tax-exempt
  compute_tax(lines, customer)           -> int     tax in cents (half up to the cent)

Units (team standard): money is an integer number of cents (1250 == $12.50);
percentages are percent numbers (10 == 10%). The pricing module, however, returns
prices in float dollars and discounts as fractions (0.10 == 10%); compute_tax
accepts the customer object exactly as pricing returns it, and converts the
discount internally. Line amounts passed to compute_tax must be in cents.
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
            # Decimal keeps exact values such as 8.875 for the arithmetic below.
            rates[region] = Decimal(row["tax_pct"].strip())
    return rates


def _load_exempt(path):
    exempt = set()
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            category = (row.get("category") or "").strip()
            if category:
                exempt.add(category)
    return exempt


_RATES = _load_rates(os.path.join(_DATA_DIR, "rates.csv"))
_EXEMPT = _load_exempt(os.path.join(_DATA_DIR, "exempt_categories.csv"))


def get_rate(region):
    """Return the sales tax percent for `region` as a percent number (8.25 == 8.25%).

    Raises KeyError if the region is not in rates.csv.
    """
    if region not in _RATES:
        raise KeyError(f"no tax rate for region {region!r}")
    return float(_RATES[region])


def is_exempt(category):
    """Return True if items in `category` are not taxed (listed in exempt_categories.csv)."""
    return category in _EXEMPT


def compute_tax(lines, customer):
    """Return the sales tax for an order, in integer cents.

    lines:    iterable of (category: str, amount_cents: int) pairs, one per order line.
              amount_cents is the line total (already multiplied by quantity).
    customer: a pricing Customer (attributes `region` and `discount`, where discount
              is a fraction, 0.10 == 10%), or None for an unknown customer.

    Rules (data_tax/RULES.md):
      1. An unknown customer (customer is None) pays 0 tax.
      2. taxable = sum of the amounts of lines whose category is not exempt.
      3. base = taxable * (100 - discount_pct) / 100
      4. tax  = base * tax_pct / 100, rounded to the cent, half up.
    Raises KeyError if the customer's region has no rate.
    """
    if customer is None:
        return 0

    taxable = 0
    for category, amount_cents in lines:
        if isinstance(amount_cents, bool) or not isinstance(amount_cents, int):
            raise TypeError(f"line amount must be an int number of cents, got {amount_cents!r}")
        if amount_cents < 0:
            raise ValueError(f"line amount must not be negative, got {amount_cents!r}")
        if not is_exempt(category):
            taxable += amount_cents

    rate = _RATES.get(customer.region)
    if rate is None:
        raise KeyError(f"no tax rate for region {customer.region!r}")

    # Pricing gives the discount as a fraction (0.10); convert to a percent number (10).
    discount = customer.discount if customer.discount is not None else 0
    discount_pct = Decimal(str(discount)) * 100

    base = Decimal(taxable) * (100 - discount_pct) / 100
    tax = base * rate / 100
    return int(tax.quantize(Decimal("1"), rounding=ROUND_HALF_UP))
