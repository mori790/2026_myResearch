"""Tax module. Owned by agent2. Computes sales tax.

The data files and rules are in data_tax/ next to this file.

Units (team coding standard):
- Money amounts are integers in cents (1250 means $12.50).
- Percentages are percent numbers (10 means 10%, 8.25 means 8.25%).
- A lookup that finds nothing raises KeyError.

Public API:
- is_exempt(category) -> bool
- tax_rate(region) -> float (percent)
- compute_tax(lines, region, discount_pct=0) -> int (cents)

Rules (data_tax/RULES.md):
- The tax percent depends on the customer's region (rates.csv).
- Items whose category is listed in exempt_categories.csv are not taxed.
- base = taxable_amount * (100 - discount_pct) / 100
- tax = base * tax_pct / 100, rounded to the cent (half up).
- An unknown customer (region None) pays 0% tax.
"""

import csv
import os
from decimal import Decimal, ROUND_HALF_UP

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_tax")
_RATES_PATH = os.path.join(_DATA_DIR, "rates.csv")
_EXEMPT_PATH = os.path.join(_DATA_DIR, "exempt_categories.csv")


def _load_rates(path):
    rates = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            region = row["region"].strip()
            rates[region] = Decimal(row["tax_pct"].strip())
    return rates


def _load_exempt(path):
    with open(path, newline="", encoding="utf-8") as f:
        return {
            row["category"].strip()
            for row in csv.DictReader(f)
            if row.get("category") and row["category"].strip()
        }


_RATES = _load_rates(_RATES_PATH)            # region -> Decimal percent
_EXEMPT_CATEGORIES = _load_exempt(_EXEMPT_PATH)  # set of category strings


def is_exempt(category):
    """Return True if items of this category are not taxed."""
    return category in _EXEMPT_CATEGORIES


def tax_rate(region):
    """Return the sales tax percent (e.g. 8.25) for a customer's region.

    region None (unknown customer) -> 0.
    A region that is not in rates.csv raises KeyError.
    """
    if region is None:
        return 0.0
    if region not in _RATES:
        raise KeyError(f"no tax rate for region {region!r}")
    return float(_RATES[region])


def compute_tax(lines, region, discount_pct=0):
    """Return the sales tax in integer cents.

    lines: iterable of (category, amount_cents) pairs, one per line item.
           amount_cents must be int. Exempt categories are excluded.
    region: customer region code (e.g. "TX"), or None for an unknown customer.
    discount_pct: customer discount as a percent number (10 means 10%).
    """
    taxable_cents = 0
    for category, amount_cents in lines:
        if isinstance(amount_cents, bool) or not isinstance(amount_cents, int):
            raise TypeError(
                f"amount_cents must be int cents, got {amount_cents!r}"
            )
        if not is_exempt(category):
            taxable_cents += amount_cents

    if isinstance(discount_pct, bool) or not isinstance(discount_pct, (int, float)):
        raise TypeError(f"discount_pct must be a percent number, got {discount_pct!r}")

    # Use Decimal (via str) to avoid binary floating-point error in money math.
    rate = Decimal(str(tax_rate(region)))
    discount = Decimal(str(discount_pct))
    base = Decimal(taxable_cents) * (Decimal(100) - discount) / Decimal(100)
    tax = base * rate / Decimal(100)
    return int(tax.quantize(Decimal("1"), rounding=ROUND_HALF_UP))
