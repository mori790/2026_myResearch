"""Tax module. Owned by agent2. Computes sales tax.

The data files and rules are in data_tax/ next to this file:
  - data_tax/rates.csv              region -> tax percent
  - data_tax/exempt_categories.csv  categories that are not taxed
  - data_tax/RULES.md               the rules implemented here

Conventions (team standard):
  - Money amounts are integers in cents (1250 means $12.50).
  - Percentages are percent numbers (10% is 10, 8.25% is 8.25).
  - A lookup that finds nothing raises KeyError.

Public API:
  tax_pct_for_region(region) -> Decimal
  is_exempt(category) -> bool
  compute_tax(lines, region, discount_pct=0) -> int   (tax in cents)
"""

import csv
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

_DATA_DIR = Path(__file__).resolve().parent / "data_tax"


def _load_rates(path):
    rates = {}
    with path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            region = row["region"].strip()
            rates[region] = Decimal(row["tax_pct"].strip())
    return rates


def _load_exempt(path):
    exempt = set()
    with path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            category = row["category"].strip()
            if category:
                exempt.add(category)
    return exempt


_RATES = _load_rates(_DATA_DIR / "rates.csv")
_EXEMPT = _load_exempt(_DATA_DIR / "exempt_categories.csv")


def tax_pct_for_region(region):
    """Return the tax percent (Decimal, e.g. Decimal('8.25')) for a region.

    Raises KeyError if the region is not listed in rates.csv.
    """
    try:
        return _RATES[region]
    except KeyError:
        raise KeyError(f"no tax rate for region {region!r}") from None


def is_exempt(category):
    """Return True if items of this category are not taxed."""
    return category in _EXEMPT


def compute_tax(lines, region, discount_pct=0):
    """Compute sales tax for an order, in integer cents.

    lines        : iterable of dicts {"category": str, "amount_cents": int},
                   where amount_cents is the line amount (price * quantity).
    region       : customer region code, or None for an unknown customer
                   (who pays 0% tax).
    discount_pct : customer discount as a percent number (e.g. 10 for 10%).

    Rules (data_tax/RULES.md):
      taxable = sum of amount_cents of non-exempt lines
      base    = taxable * (100 - discount_pct) / 100
      tax     = base * tax_pct / 100, rounded to the cent (half up)

    Raises KeyError if region is not None and is not in rates.csv.
    """
    if region is None:
        return 0

    pct = tax_pct_for_region(region)

    taxable = 0
    for line in lines:
        if not is_exempt(line["category"]):
            taxable += int(line["amount_cents"])

    discount = Decimal(str(discount_pct))

    # Exact arithmetic; round only once, at the end.
    tax = (Decimal(taxable) * (Decimal(100) - discount) * pct) / Decimal(10000)
    return int(tax.quantize(Decimal("1"), rounding=ROUND_HALF_UP))
