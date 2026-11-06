"""Tax module. Owned by agent2. Computes sales tax.

The data files and rules are in data_tax/ next to this file:
  - data_tax/rates.csv              region -> tax percent
  - data_tax/exempt_categories.csv  categories that are not taxed
  - data_tax/RULES.md               the rules this module implements

Team conventions (committed in the decision log as TAX_API and
TAX_UNKNOWN_CUSTOMER):
  - Money is an integer number of cents (1250 == $12.50).
  - Percentages are percent numbers (10 == 10%, 8.25 == 8.25%).
  - A lookup that finds nothing raises KeyError, except that a region of
    None means "unknown customer" and is taxed at 0%.

Public API:
  compute_tax(region, lines, discount_pct=0) -> int (cents)
  tax_rate_pct(region) -> Decimal (percent)
"""

import csv
import os
from decimal import Decimal, ROUND_HALF_UP

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_tax")
_RATES_PATH = os.path.join(_DATA_DIR, "rates.csv")
_EXEMPT_PATH = os.path.join(_DATA_DIR, "exempt_categories.csv")

_HUNDRED = Decimal(100)


def _load_rates(path):
    rates = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            region = row["region"].strip()
            if not region:
                continue
            rates[region] = Decimal(row["tax_pct"].strip())
    return rates


def _load_exempt(path):
    exempt = set()
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            category = (row.get("category") or "").strip()
            if category:
                exempt.add(category)
    return frozenset(exempt)


_RATES = _load_rates(_RATES_PATH)          # region -> Decimal percent
_EXEMPT = _load_exempt(_EXEMPT_PATH)       # frozenset of category strings


def tax_rate_pct(region):
    """Return the tax rate for a region as a Decimal percent (8.25 == 8.25%).

    region=None means the customer is unknown; the rate is 0.
    An unknown non-None region raises KeyError.
    """
    if region is None:
        return Decimal(0)
    return _RATES[region]


def compute_tax(region, lines, discount_pct=0):
    """Compute the sales tax for an order, in integer cents.

    Arguments:
      region       -- customer region code such as "TX", or None for an
                      unknown customer (0% tax).
      lines        -- iterable of (category, amount_cents) pairs, one per
                      order line, before discount. Lines whose category is
                      in data_tax/exempt_categories.csv are not taxed.
      discount_pct -- customer discount as a percent number (10 == 10%).

    Rules (data_tax/RULES.md):
      taxable = sum of amounts of non-exempt lines
      base    = taxable * (100 - discount_pct) / 100
      tax     = base * tax_pct / 100, rounded to the cent (half up)

    Returns the tax amount only, as an int number of cents.
    Raises KeyError for an unknown non-None region.
    """
    rate = tax_rate_pct(region)  # raises KeyError for unknown region

    taxable = 0
    for category, amount_cents in lines:
        if not isinstance(amount_cents, int):
            raise TypeError("amount_cents must be an int, got %r" % (amount_cents,))
        if category not in _EXEMPT:
            taxable += amount_cents

    discount = Decimal(str(discount_pct))
    base = Decimal(taxable) * (_HUNDRED - discount) / _HUNDRED
    tax = base * rate / _HUNDRED
    return int(tax.quantize(Decimal(1), rounding=ROUND_HALF_UP))
