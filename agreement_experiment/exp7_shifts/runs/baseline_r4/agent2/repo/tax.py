"""Tax module. Owned by agent2. Computes sales tax.

The data files and rules are in data_tax/ next to this file (see data_tax/RULES.md).

Conventions (team standard):
  * Money amounts are integers in cents (1250 means $12.50).
  * Percentages are percent numbers (10 means 10%, 8.25 means 8.25%).
  * A lookup that finds nothing raises KeyError.
    Exception: region=None means "unknown customer", which pays 0% tax (RULES.md).

Public API:
  get_tax_pct(region)                          -> float percent (KeyError if region unknown)
  is_exempt(category)                          -> bool
  compute_tax(lines, region, discount_pct=0)   -> int cents
"""

import csv
import os
from decimal import Decimal, ROUND_HALF_UP

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_tax")
_RATES_PATH = os.path.join(_DATA_DIR, "rates.csv")
_EXEMPT_PATH = os.path.join(_DATA_DIR, "exempt_categories.csv")


def _load_rates(path):
    """Return {region: Decimal percent} from rates.csv (columns: region,tax_pct)."""
    rates = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            region = row["region"].strip()
            if not region:
                continue
            # Parse from the string so 8.25 is exactly 8.25 (no binary float error).
            rates[region] = Decimal(row["tax_pct"].strip())
    return rates


def _load_exempt(path):
    """Return the set of exempt categories (normalized to lowercase, stripped)."""
    exempt = set()
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            category = (row.get("category") or "").strip().lower()
            if category:
                exempt.add(category)
    return exempt


_RATES = _load_rates(_RATES_PATH)
_EXEMPT = _load_exempt(_EXEMPT_PATH)


def get_tax_pct(region):
    """Return the sales tax percent for a customer region (e.g. 'TX' -> 8.25).

    region=None means the customer is unknown, which pays 0% tax.
    An unknown (non-None) region raises KeyError.
    """
    if region is None:
        return 0.0
    return float(_RATES[region])


def is_exempt(category):
    """True if items of this category are not taxed (listed in exempt_categories.csv)."""
    if category is None:
        return False
    return str(category).strip().lower() in _EXEMPT


def compute_tax(lines, region, discount_pct=0):
    """Compute sales tax in integer cents.

    lines:        iterable of (category, amount_cents) pairs. amount_cents is the
                  pre-discount line amount (integer cents).
    region:       customer region string (e.g. 'TX'), or None for an unknown customer.
    discount_pct: customer discount as a percent number (e.g. 10 means 10% off).

    Rule (RULES.md):
      taxable_amount = sum of amounts of non-exempt lines
      base           = taxable_amount * (100 - discount_pct) / 100
      tax            = base * tax_pct / 100, rounded to the cent (half up)
    """
    if discount_pct is None:
        discount_pct = 0
    discount = Decimal(str(discount_pct))
    if discount < 0 or discount > 100:
        raise ValueError(f"discount_pct must be between 0 and 100, got {discount_pct!r}")

    taxable_cents = 0
    for category, amount_cents in lines:
        if not isinstance(amount_cents, int) or isinstance(amount_cents, bool):
            raise TypeError(f"amount_cents must be an int (cents), got {amount_cents!r}")
        if not is_exempt(category):
            taxable_cents += amount_cents

    if region is None:
        return 0  # unknown customer pays 0% tax

    rate = _RATES[region]  # KeyError for an unknown region, per team convention

    base = Decimal(taxable_cents) * (Decimal(100) - discount) / Decimal(100)
    tax = base * rate / Decimal(100)
    return int(tax.quantize(Decimal("1"), rounding=ROUND_HALF_UP))
