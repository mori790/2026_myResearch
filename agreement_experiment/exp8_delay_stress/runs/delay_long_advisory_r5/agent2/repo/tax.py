"""Tax module. Owned by agent2. Computes sales tax.

Contract (committed decisions in the shared log):
- Money is integer cents (1250 = $12.50). Percentages are percent numbers (8.25 = 8.25%).
- compute_tax(region, discount_pct, lines) -> int cents, rounded half up.
  - region: customer region as in data_tax/rates.csv. None = unknown customer -> 0 tax.
    A non-None region with no rate row raises KeyError (a mistyped region must not become 0% tax).
  - discount_pct: customer discount percent (10 = 10% off); tax applies it to the taxable amount.
  - lines: iterable of (category, amount_cents). Categories listed in exempt_categories.csv are not taxed.
- tax_percent(region) -> float: rate from rates.csv; raises KeyError if the region is not found.
  None (unknown customer) -> 0.0.

Data and rules are in data_tax/ next to this file (see data_tax/RULES.md).
"""

import csv
import os
from decimal import Decimal, ROUND_HALF_UP

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_tax")


def _load_rates():
    """Read data_tax/rates.csv into {region: tax_pct as Decimal}."""
    rates = {}
    with open(os.path.join(_DATA_DIR, "rates.csv"), newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            region = row["region"].strip()
            rates[region] = Decimal(row["tax_pct"].strip())
    return rates


def _load_exempt_categories():
    """Read data_tax/exempt_categories.csv into a set of category names."""
    exempt = set()
    with open(os.path.join(_DATA_DIR, "exempt_categories.csv"), newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            category = row["category"].strip()
            if category:
                exempt.add(category)
    return exempt


_RATES = _load_rates()
_EXEMPT_CATEGORIES = _load_exempt_categories()


def tax_percent(region):
    """Return the sales tax percent for a region (e.g. 'TX' -> 8.25).

    None means unknown customer and gives 0.0. An unknown region raises KeyError.
    """
    if region is None:
        return 0.0
    return float(_RATES[region])


def _check_cents(value, what):
    # Money must be integer cents. Reject floats so a unit mismatch fails loudly.
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{what} must be an integer number of cents, got {value!r}")


def compute_tax(region, discount_pct, lines):
    """Return the total sales tax for an order, in integer cents, rounded half up.

    Steps (RULES.md):
      1. taxable = sum of line amounts whose category is not exempt.
      2. base = taxable * (100 - discount_pct) / 100.
      3. tax = base * tax_pct / 100, rounded to the cent (half up).
    """
    if region is None:
        # Unknown customer pays no tax (RULES.md). Lines are still validated below.
        rate = None
    else:
        rate = _RATES[region]  # KeyError for an unknown region

    taxable_cents = 0
    for category, amount_cents in lines:
        _check_cents(amount_cents, "line amount")
        if category in _EXEMPT_CATEGORIES:
            continue
        taxable_cents += amount_cents

    if rate is None:
        return 0

    if isinstance(discount_pct, bool) or not isinstance(discount_pct, (int, float, Decimal)):
        raise TypeError(f"discount_pct must be a percent number, got {discount_pct!r}")
    discount = Decimal(str(discount_pct))

    base = Decimal(taxable_cents) * (Decimal(100) - discount) / Decimal(100)
    tax = base * rate / Decimal(100)
    return int(tax.quantize(Decimal("1"), rounding=ROUND_HALF_UP))
