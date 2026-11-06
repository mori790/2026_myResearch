"""Tax module. Owned by agent2. Computes sales tax.

The data files and rules are in data_tax/ next to this file:
  - rates.csv               : region -> tax percent (e.g. TX 8.25)
  - exempt_categories.csv   : categories that are not taxed (e.g. food)
  - RULES.md                : the tax rules

Units (team decisions TAX_API, TAX_RATE, UNKNOWN_CUSTOMER_TAX):
  - money amounts are int cents (1250 = $12.50)
  - percentages are fractions (0.10 = 10%) in the public API. The CSV holds
    percent numbers (8.25); they are converted once at load time.

Public functions:
  compute_tax(region, lines, discount) -> int    tax in cents
  tax_rate(region) -> float                      tax rate as a fraction
"""

import csv
import os
from decimal import Decimal, ROUND_HALF_UP

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_tax")


def _load_rates():
    """Return {region: Decimal fraction}, e.g. {'TX': Decimal('0.0825')}."""
    rates = {}
    path = os.path.join(_DATA_DIR, "rates.csv")
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            region = row["region"].strip()
            # The CSV is in percent numbers; Decimal keeps the value exact.
            rates[region] = Decimal(row["tax_pct"].strip()) / Decimal(100)
    return rates


def _load_exempt_categories():
    """Return the set of exempt categories, normalized to lowercase."""
    exempt = set()
    path = os.path.join(_DATA_DIR, "exempt_categories.csv")
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            exempt.add(row["category"].strip().lower())
    return exempt


_RATES = _load_rates()
_EXEMPT = _load_exempt_categories()


def _normalize_category(category):
    return str(category).strip().lower()


def tax_rate(region):
    """Return the sales tax rate for a customer region as a fraction.

    0.0825 means 8.25%. region None (unknown customer) gives 0.0.
    Raises KeyError if region is a code that is not in rates.csv.
    """
    if region is None:
        return 0.0
    return float(_RATES[region])


def compute_tax(region, lines, discount):
    """Return the sales tax for an order, in int cents.

    region   : customer region code (e.g. "TX"), or None for an unknown customer.
    lines    : list of {"category": str, "amount_cents": int} for ALL line items.
               Exempt categories are dropped here.
    discount : customer discount as a fraction (0.10 = 10%), 0 if none.

    Rules (data_tax/RULES.md):
      taxable = sum of amount_cents of non-exempt lines
      base    = taxable * (1 - discount)
      tax     = base * rate, rounded to the cent (half up)

    Raises KeyError if region is not None and not in rates.csv.
    """
    # Check the region first so an invalid region is always reported,
    # even when the order has no taxable lines.
    if region is None:
        rate = Decimal(0)
    else:
        rate = _RATES[region]  # KeyError for an unknown region code

    discount_fraction = Decimal(str(discount))
    if discount_fraction < 0 or discount_fraction > 1:
        raise ValueError(f"discount must be a fraction between 0 and 1, got {discount!r}")

    taxable_cents = 0
    for line in lines:
        if _normalize_category(line["category"]) in _EXEMPT:
            continue
        amount = line["amount_cents"]
        if isinstance(amount, bool) or not isinstance(amount, int):
            raise TypeError(f"amount_cents must be int, got {amount!r}")
        taxable_cents += amount

    if region is None or taxable_cents == 0:
        return 0

    base = Decimal(taxable_cents) * (Decimal(1) - discount_fraction)
    tax = base * rate
    return int(tax.quantize(Decimal("1"), rounding=ROUND_HALF_UP))
