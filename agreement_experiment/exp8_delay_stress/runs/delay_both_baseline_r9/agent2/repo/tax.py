"""Tax module. Owned by agent2. Computes sales tax.

The data files and rules are in data_tax/ next to this file (see data_tax/RULES.md).

Conventions (team standard):
  - Money amounts are integers in cents (1250 means $12.50).
  - Percentages are percent numbers (10 means 10%, 8.25 means 8.25%).
  - A lookup that finds nothing raises KeyError.

Public API:
  get_tax_pct(region)                      -> Decimal   tax percent for a region
  is_exempt(category)                      -> bool      True if the category is tax-exempt
  compute_tax(region, lines, discount_pct) -> int       sales tax in cents

  region        : region code string such as "TX", "NY", "OR", or None for an
                  unknown customer (None pays 0% tax).
  lines         : iterable of (category, amount_cents) pairs, one per line item,
                  where amount_cents is the line total in integer cents.
  discount_pct  : customer discount in percent (0..100), e.g. 10 for 10% off.
"""

import csv
import os
from decimal import Decimal, ROUND_HALF_UP

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_tax")
_RATES_PATH = os.path.join(_DATA_DIR, "rates.csv")
_EXEMPT_PATH = os.path.join(_DATA_DIR, "exempt_categories.csv")


def _norm(value):
    return str(value).strip().lower()


def _load_rates(path):
    rates = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            region = row["region"].strip()
            # Decimal from the string avoids float artifacts such as 8.875 -> 8.87499...
            rates[region] = Decimal(row["tax_pct"].strip())
    return rates


def _load_exempt(path):
    exempt = set()
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            category = row["category"].strip()
            if category:
                exempt.add(_norm(category))
    return exempt


_RATES = _load_rates(_RATES_PATH)
_EXEMPT = _load_exempt(_EXEMPT_PATH)


def get_tax_pct(region):
    """Return the tax percent (Decimal) for a region.

    None (unknown customer) -> 0.
    A region code not present in rates.csv -> KeyError.
    """
    if region is None:
        return Decimal("0")
    try:
        return _RATES[region.strip()]
    except KeyError:
        raise KeyError(f"no tax rate for region {region!r}") from None


def is_exempt(category):
    """True if items of this category are not taxed (listed in exempt_categories.csv)."""
    return _norm(category) in _EXEMPT


def compute_tax(region, lines, discount_pct):
    """Return the sales tax in integer cents.

    Rule (data_tax/RULES.md):
      taxable_amount = sum of line amounts whose category is not exempt
      base           = taxable_amount * (100 - discount_pct) / 100
      tax            = base * tax_pct / 100, rounded to the cent (half up)
    """
    discount = Decimal(str(discount_pct))
    if discount < 0 or discount > 100:
        raise ValueError(f"discount_pct must be between 0 and 100, got {discount_pct!r}")

    taxable_cents = 0
    for category, amount_cents in lines:
        if not isinstance(amount_cents, int):
            raise TypeError(f"amount_cents must be an int (cents), got {amount_cents!r}")
        if not is_exempt(category):
            taxable_cents += amount_cents

    tax_pct = get_tax_pct(region)

    # Exact arithmetic: base is not rounded before the tax is computed.
    tax = (Decimal(taxable_cents) * (Decimal(100) - discount) / Decimal(100)
           * tax_pct / Decimal(100))
    return int(tax.quantize(Decimal("1"), rounding=ROUND_HALF_UP))
