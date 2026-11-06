"""Tax module. Owned by agent2. Computes sales tax. The data files and rules are in data_tax/ next to this file.

Team conventions (committed decisions):
  - Money is float dollars (12.5 means $12.50). Tax is rounded half up to the cent.
  - Percentages are fractions (0.10 means 10%). rates.csv stores percent numbers; they are converted here.
  - A lookup that finds nothing returns None (it does not raise).

Public API:
  rate(region) -> float | None
      Tax rate as a fraction (0.0825 for TX). None region (unknown customer) -> 0.0.
      Non-null region not in rates.csv -> None.
  compute_tax(lines, region, discount) -> float
      lines: iterable of {"amount": float dollars, "category": str or None}
             (amount = qty * unit price, computed by the caller; category None => taxable)
      region: customer region string, or None for an unknown customer (0 tax).
      discount: customer discount as a fraction (0.10 = 10%); 0.0 if none.
      Returns the tax in float dollars, rounded half up to the cent.
      Rule: base = (sum of taxable line amounts) * (1 - discount); tax = base * rate.
      A non-null region not in rates.csv is charged 0 tax (no rate is known).
"""

import csv
import os
from decimal import Decimal, ROUND_HALF_UP

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_tax")
_CENT = Decimal("0.01")


def _load_rates(path):
    rates = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            region = row["region"].strip()
            if not region:
                continue
            # rates.csv stores percent numbers (8.25 means 8.25%); keep an exact fraction.
            rates[region] = Decimal(row["tax_pct"].strip()) / Decimal(100)
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


def _to_decimal(value):
    # Convert via str() so that 0.1 becomes exactly Decimal("0.1") and not the binary float value.
    return Decimal(str(value))


def rate(region):
    """Return the tax rate as a fraction, 0.0 for an unknown customer (None), or None if the region is unknown."""
    if region is None:
        return 0.0
    value = _RATES.get(region)
    if value is None:
        return None
    return float(value)


def is_exempt(category):
    """True if items in this category are not taxed. A None category is taxable."""
    return category is not None and category in _EXEMPT


def compute_tax(lines, region, discount):
    """Compute sales tax in float dollars, rounded half up to the cent."""
    taxable = Decimal(0)
    for line in lines:
        if is_exempt(line.get("category")):
            continue
        taxable += _to_decimal(line["amount"])

    discount_fraction = _to_decimal(discount) if discount else Decimal(0)
    base = taxable * (Decimal(1) - discount_fraction)

    if region is None or region not in _RATES:
        # Unknown customer, or a region with no known rate: 0 tax.
        return 0.0

    tax = base * _RATES[region]
    return float(tax.quantize(_CENT, rounding=ROUND_HALF_UP))
