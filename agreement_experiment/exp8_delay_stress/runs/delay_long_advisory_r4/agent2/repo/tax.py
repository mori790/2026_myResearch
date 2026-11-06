"""Tax module. Owned by agent2. Computes sales tax. The data files and rules are in data_tax/ next to this file.

Committed API (TAX_API v2):
    compute_tax_cents(lines, region, discount_pct) -> int
    tax_pct(region) -> float

Conventions (team standard):
    - Money is an integer number of cents (1250 == $12.50).
    - Percentages are percent numbers (10 == 10%, 8.25 == 8.25%).
    - A lookup that finds nothing raises KeyError.
"""

import csv
import os
from fractions import Fraction

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_tax")


def _load_rates(path):
    rates = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            region = row["region"].strip()
            # Keep the exact decimal text so 8.875 is not stored as a binary float.
            rates[region] = Fraction(row["tax_pct"].strip())
    return rates


def _load_exempt(path):
    exempt = set()
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            category = row["category"].strip()
            if category:
                exempt.add(category)
    return exempt


_RATES = _load_rates(os.path.join(_DATA_DIR, "rates.csv"))          # region -> Fraction percent
_EXEMPT = _load_exempt(os.path.join(_DATA_DIR, "exempt_categories.csv"))  # set of category names


def tax_pct(region):
    """Return the sales tax percent for a region, e.g. 8.25 for 8.25%.

    Raises KeyError if the region is not listed in rates.csv.
    """
    return float(_RATES[region])


def _round_half_up(x):
    """Round a Fraction to the nearest integer, halves away from zero."""
    if x >= 0:
        return (x + Fraction(1, 2)).__floor__()
    return -((-x + Fraction(1, 2)).__floor__())


def compute_tax_cents(lines, region, discount_pct):
    """Return the sales tax for an order, in integer cents.

    lines        -- list of {"amount_cents": int, "category": str}; line totals before tax.
    region       -- customer's region code (e.g. "TX"), or None when the customer has no
                    region on file (unknown customer), which means no tax (0 cents).
    discount_pct -- customer's discount as a percent number (10 == 10% off).

    Rules (data_tax/RULES.md):
        taxable = sum of amount_cents of lines whose category is NOT exempt
        base    = taxable * (100 - discount_pct) / 100
        tax     = base * tax_pct / 100, rounded to the nearest cent (half up)

    Raises KeyError if region is not None and not listed in rates.csv.
    Raises ValueError if discount_pct is outside [0, 100] or an amount is not an int.
    """
    discount = Fraction(str(discount_pct))
    if not 0 <= discount <= 100:
        raise ValueError(f"discount_pct must be between 0 and 100, got {discount_pct!r}")

    if region is None:
        return 0

    rate = _RATES[region]  # KeyError for unknown regions

    taxable = 0
    for line in lines:
        amount = line["amount_cents"]
        if isinstance(amount, bool) or not isinstance(amount, int):
            raise ValueError(f"amount_cents must be an int, got {amount!r}")
        if line["category"] not in _EXEMPT:
            taxable += amount

    base = Fraction(taxable) * (100 - discount) / 100
    tax = base * rate / 100
    return _round_half_up(tax)
