"""Tax module. Owned by agent2. Computes sales tax.

The data files and rules are in data_tax/ next to this file.

Public API (proposed as topic 'tax_api' in the team agreement log):

    tax_pct(region)                          -> float  (percent number, e.g. 8.25)
    is_exempt(category)                      -> bool
    compute_tax(region, lines, discount_pct) -> int    (tax in integer cents)

Conventions:
    * Money is integer cents (1250 == $12.50).
    * Percentages are percent numbers (10% is 10, 8.25% is 8.25).
    * A lookup that finds nothing raises KeyError.
    * Unknown customer (region None or empty) pays 0% tax.
"""

import csv
import os
from decimal import ROUND_HALF_UP, Decimal

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_tax")


def _load_rates(path):
    rates = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            rates[row["region"].strip().upper()] = Decimal(row["tax_pct"].strip())
    return rates


def _load_exempt(path):
    exempt = set()
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            exempt.add(row["category"].strip().lower())
    return exempt


_RATES = _load_rates(os.path.join(_DATA_DIR, "rates.csv"))
_EXEMPT = _load_exempt(os.path.join(_DATA_DIR, "exempt_categories.csv"))


def _is_unknown_customer(region):
    return region is None or str(region).strip() == ""


def tax_pct(region):
    """Return the sales tax percent for a customer region (e.g. 8.25 for 'TX').

    region None or empty means an unknown customer: 0 is returned.
    A non-empty region that is not in rates.csv raises KeyError.
    """
    if _is_unknown_customer(region):
        return 0.0
    key = str(region).strip().upper()
    if key not in _RATES:
        raise KeyError(f"no tax rate for region {region!r}")
    return float(_RATES[key])


def is_exempt(category):
    """Return True if items in this category are not taxed (see exempt_categories.csv)."""
    return str(category).strip().lower() in _EXEMPT


def compute_tax(region, lines, discount_pct=0):
    """Compute sales tax in integer cents.

    region       : customer region code (e.g. 'TX'); None/'' for unknown customer (0% tax).
    lines        : iterable of (category, line_amount_cents) pairs, amounts taken
                   before the customer's discount. Exempt categories are skipped.
    discount_pct : customer discount as a percent number (e.g. 10 for 10% off).

    Rules (data_tax/RULES.md):
        taxable = sum of non-exempt line amounts
        base    = taxable * (100 - discount_pct) / 100
        tax     = base * tax_pct / 100, rounded to the cent, half up.
    """
    taxable = 0
    for category, amount_cents in lines:
        if not is_exempt(category):
            taxable += int(amount_cents)

    discount = Decimal(str(discount_pct))
    if discount < 0 or discount > 100:
        raise ValueError(f"discount_pct must be between 0 and 100, got {discount_pct!r}")

    rate = Decimal(str(tax_pct(region)))
    base = Decimal(taxable) * (Decimal(100) - discount) / Decimal(100)
    tax = base * rate / Decimal(100)
    return int(tax.quantize(Decimal("1"), rounding=ROUND_HALF_UP))
