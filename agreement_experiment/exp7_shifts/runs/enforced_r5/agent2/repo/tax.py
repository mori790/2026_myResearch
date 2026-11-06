"""Tax module. Owned by agent2. Computes sales tax.

The data files and rules are in data_tax/ next to this file (see data_tax/RULES.md).

Conventions (team standard):
  * Money amounts are integers in cents (1250 means $12.50).
  * Percentages are percent numbers (10% is 10, 8.25% is 8.25).
  * A lookup that finds nothing raises KeyError.

This module does NOT look up items or customers. The caller (invoice.py) passes in
the taxable line amounts, the customer's region, and the customer's discount percent.
"""

import csv
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

_DATA_DIR = Path(__file__).resolve().parent / "data_tax"


def _load_rates(path):
    """Return {region: Decimal tax_pct} from rates.csv (columns: region,tax_pct)."""
    rates = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            region = row["region"].strip()
            rates[region] = Decimal(row["tax_pct"].strip())
    return rates


def _load_exempt(path):
    """Return the set of exempt category names from exempt_categories.csv (column: category)."""
    exempt = set()
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            name = row["category"].strip()
            if name:
                exempt.add(name)
    return exempt


_RATES = _load_rates(_DATA_DIR / "rates.csv")
_EXEMPT = _load_exempt(_DATA_DIR / "exempt_categories.csv")


def get_tax_pct(region):
    """Return the sales tax percent (percent number, e.g. 8.25) for a region.

    region=None means the customer is unknown; an unknown customer pays 0% tax.
    Raises KeyError if the region is given but has no rate in rates.csv.
    """
    if region is None:
        return 0.0
    return float(_RATES[region])


def is_exempt(category):
    """Return True if items in this category are not taxed (exempt_categories.csv)."""
    return category in _EXEMPT


def taxable_amount_cents(lines):
    """Sum the amounts of the non-exempt lines.

    lines: iterable of dicts {"category": str, "amount_cents": int}
    Returns an int number of cents.
    """
    total = 0
    for line in lines:
        if not is_exempt(line["category"]):
            total += int(line["amount_cents"])
    return total


def compute_tax_cents(lines, region, discount_pct):
    """Compute the sales tax for an order, in integer cents.

    lines        : iterable of {"category": str, "amount_cents": int}
    region       : customer's region code (e.g. "TX"), or None for an unknown customer
    discount_pct : customer's discount as a percent number (10 means 10%), 0 for none

    Rules (data_tax/RULES.md):
      taxable    = sum of non-exempt line amounts (cents)
      base       = taxable * (100 - discount_pct) / 100
      tax        = base * tax_pct / 100, rounded to the nearest cent (half up)

    Unknown region (None) -> tax 0. A region with no rate raises KeyError.
    """
    discount = Decimal(str(discount_pct))
    if discount < 0 or discount > 100:
        raise ValueError("discount_pct must be between 0 and 100, got %r" % (discount_pct,))

    taxable = taxable_amount_cents(lines)
    if region is None:
        return 0

    rate = _RATES[region]  # KeyError if the region is unknown
    base = Decimal(taxable) * (Decimal(100) - discount) / Decimal(100)
    tax = base * rate / Decimal(100)
    return int(tax.quantize(Decimal(1), rounding=ROUND_HALF_UP))
