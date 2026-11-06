"""Tax module. Owned by agent2. Computes sales tax.

The data files and rules are in data_tax/ next to this file:
  - data_tax/rates.csv                 region -> tax percent
  - data_tax/exempt_categories.csv     categories that are not taxed
  - data_tax/RULES.md                  the rules implemented here

Conventions (team standard):
  - Money amounts are integers in cents (1250 means $12.50).
  - Percentages are percent numbers (10% is 10, 8.25% is 8.25).
  - A lookup that finds nothing raises KeyError.

Public API (agreed on topic 'tax_api'):
  tax_pct(region)                              -> float
  is_taxable(category)                         -> bool
  compute_tax(lines, region, discount_pct=0)   -> int (cents)
"""

import csv
import os
from decimal import ROUND_HALF_UP, Decimal

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_tax")
_RATES_PATH = os.path.join(_DATA_DIR, "rates.csv")
_EXEMPT_PATH = os.path.join(_DATA_DIR, "exempt_categories.csv")


def _load_rates(path=_RATES_PATH):
    """Return {region: Decimal percent} from rates.csv."""
    rates = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            region = row["region"].strip()
            rates[region] = Decimal(row["tax_pct"].strip())
    return rates


def _load_exempt(path=_EXEMPT_PATH):
    """Return the set of tax-exempt categories from exempt_categories.csv."""
    exempt = set()
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            category = (row.get("category") or "").strip()
            if category:
                exempt.add(category)
    return exempt


_RATES = _load_rates()
_EXEMPT = _load_exempt()


def _rate_for(region):
    """Return the tax percent as Decimal. region None (unknown customer) -> 0.

    A non-None region that is not in rates.csv raises KeyError.
    """
    if region is None:
        return Decimal("0")
    return _RATES[region]


def tax_pct(region):
    """Return the sales tax percent (e.g. 8.25) for a customer's region.

    region None means the customer is unknown, so the rate is 0.
    An unknown non-None region raises KeyError.
    """
    return float(_rate_for(region))


def is_taxable(category):
    """Return False if the item category is exempt (e.g. 'food'), else True."""
    return category not in _EXEMPT


def compute_tax(lines, region, discount_pct=0):
    """Compute sales tax in integer cents.

    lines: iterable of (category, amount_cents) pairs, one per line item.
    region: customer region (str), or None for an unknown customer (0% tax).
    discount_pct: customer discount as a percent number (e.g. 10 for 10%).

    Rules (RULES.md):
      taxable_amount = sum of amounts of non-exempt line items
      base           = taxable_amount * (100 - discount_pct) / 100
      tax            = base * tax_pct / 100, rounded to the cent (half up)
    """
    taxable_cents = 0
    for category, amount_cents in lines:
        if not isinstance(amount_cents, int) or isinstance(amount_cents, bool):
            raise TypeError(f"amount_cents must be an int (cents), got {amount_cents!r}")
        if is_taxable(category):
            taxable_cents += amount_cents

    discount = Decimal(str(discount_pct))
    if not Decimal("0") <= discount <= Decimal("100"):
        raise ValueError(f"discount_pct must be between 0 and 100, got {discount_pct!r}")

    rate = _rate_for(region)
    base = Decimal(taxable_cents) * (Decimal("100") - discount) / Decimal("100")
    tax = base * rate / Decimal("100")
    return int(tax.quantize(Decimal("1"), rounding=ROUND_HALF_UP))
