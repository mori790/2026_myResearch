"""Tax module. Owned by agent2. Computes sales tax.

The data files and rules are in data_tax/ next to this file:
  - data_tax/rates.csv             region -> tax_pct (percent number, e.g. 8.25)
  - data_tax/exempt_categories.csv categories that are not taxed
  - data_tax/RULES.md              the tax rules

Team conventions (see decision log topic "tax_api"):
  - Money amounts are integers in cents (1250 means $12.50).
  - Percentages are percent numbers (10 means 10%, 8.25 means 8.25%).
  - A lookup that finds nothing raises KeyError.

Rules implemented here:
  - taxable_sum = sum of line amounts whose category is NOT exempt.
  - base  = taxable_sum * (100 - discount_pct) / 100
  - tax   = base * tax_pct / 100, rounded to the cent (half up).
  - An unknown customer (region is None) pays 0% tax.
"""

import csv
import os
from decimal import Decimal, ROUND_HALF_UP

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_tax")


def _norm_category(category):
    return str(category).strip().lower()


def _load_rates(path):
    rates = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            region = row["region"].strip()
            if region in rates:
                raise ValueError(f"duplicate region in rates.csv: {region!r}")
            # Decimal keeps values like 8.875 exact (no binary float error).
            rates[region] = Decimal(row["tax_pct"].strip())
    return rates


def _load_exempt(path):
    exempt = set()
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            exempt.add(_norm_category(row["category"]))
    return exempt


_RATES = _load_rates(os.path.join(_DATA_DIR, "rates.csv"))
_EXEMPT = _load_exempt(os.path.join(_DATA_DIR, "exempt_categories.csv"))


def tax_pct(region):
    """Return the sales tax percent for a region, e.g. 8.25.

    Raises KeyError if the region is not in rates.csv.
    """
    if region not in _RATES:
        raise KeyError(f"no tax rate for region {region!r}")
    return float(_RATES[region])


def is_exempt(category):
    """True if items of this category are not taxed (exempt_categories.csv)."""
    return _norm_category(category) in _EXEMPT


def _check_cents(value, what):
    # bool is a subclass of int, so reject it explicitly.
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{what} must be an int number of cents, got {value!r}")
    if value < 0:
        raise ValueError(f"{what} must not be negative, got {value!r}")


def compute_tax(lines, region, discount_pct=0):
    """Compute the sales tax for one order, in integer cents.

    lines        : iterable of (category, amount_cents) pairs, one per line item.
                   amount_cents is the line total in cents (int, >= 0).
    region       : the customer's region (str, e.g. "TX"), or None when the
                   customer is unknown. Unknown customer -> tax is 0.
    discount_pct : the customer's discount as a percent number (int or float,
                   e.g. 10 for 10%). Must be in [0, 100]. Default 0.

    Returns the tax amount in integer cents (rounded half up to the cent).

    Raises KeyError if region is not None and is not in rates.csv.
    """
    taxable_cents = 0
    for category, amount_cents in lines:
        _check_cents(amount_cents, "line amount")
        if not is_exempt(category):
            taxable_cents += amount_cents

    if region is None:
        # Unknown customer pays 0% tax (RULES.md).
        return 0

    if region not in _RATES:
        raise KeyError(f"no tax rate for region {region!r}")
    rate = _RATES[region]

    discount = Decimal(str(discount_pct))
    if discount < 0 or discount > 100:
        raise ValueError(f"discount_pct must be in [0, 100], got {discount_pct!r}")

    # base = taxable * (100 - d) / 100 ; tax = base * r / 100
    #      = taxable * (100 - d) * r / 10000
    # Exact Decimal arithmetic, then a single rounding step.
    tax = (
        Decimal(taxable_cents) * (Decimal(100) - discount) * rate / Decimal(10000)
    )
    return int(tax.quantize(Decimal(1), rounding=ROUND_HALF_UP))
