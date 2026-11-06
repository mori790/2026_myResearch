"""Tax module. Owned by agent2. Computes sales tax.

The data files and rules are in data_tax/ next to this file.

Public API (committed decision `tax_api` v1):
    compute_tax(region, lines, discount_pct=0) -> int   # tax in integer cents
    tax_rate(region) -> float                           # percent number
    is_exempt(category) -> bool

Conventions (team standard):
    * money amounts are integer cents (1250 == $12.50)
    * percentages are percent numbers (10 == 10%, 8.25 == 8.25%)
    * a lookup that finds nothing raises KeyError
    * region None means "unknown customer": tax 0 (RULES.md)
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
            # Decimal(str) keeps the exact value of e.g. "8.875".
            rates[region] = Decimal(row["tax_pct"].strip())
    return rates


def _load_exempt(path):
    with open(path, newline="", encoding="utf-8") as f:
        return {row["category"].strip() for row in csv.DictReader(f) if row["category"].strip()}


_RATES = _load_rates(_RATES_PATH)
_EXEMPT = _load_exempt(_EXEMPT_PATH)


def tax_rate(region):
    """Return the sales tax percent for a region (e.g. 8.25 for "TX").

    region None (unknown customer) -> 0.
    An unrecognised non-None region raises KeyError.
    """
    if region is None:
        return 0.0
    if region not in _RATES:
        raise KeyError(f"unknown tax region: {region!r}")
    return float(_RATES[region])


def is_exempt(category):
    """True if items in this category are not taxed (listed in exempt_categories.csv).

    Categories not listed are taxable.
    """
    return category in _EXEMPT


def compute_tax(region, lines, discount_pct=0):
    """Compute sales tax for an order, in integer cents.

    region       : region code from rates.csv, or None for an unknown customer (tax 0).
    lines        : iterable of (category, amount_cents) for every line of the order.
    discount_pct : customer discount in percent numbers (10 == 10%), applied to the
                   taxable sum only.

    Rule (RULES.md):
        taxable = sum of amounts of non-exempt lines
        base    = taxable * (100 - discount_pct) / 100
        tax     = base * tax_pct / 100, rounded half up to the cent

    The tax is computed once on the order total of taxable lines, not per line.
    """
    taxable_cents = 0
    for category, amount_cents in lines:
        if not isinstance(amount_cents, int) or isinstance(amount_cents, bool):
            raise TypeError(f"amount_cents must be an int (cents), got {amount_cents!r}")
        if not is_exempt(category):
            taxable_cents += amount_cents

    if region is None:
        return 0

    if region not in _RATES:
        raise KeyError(f"unknown tax region: {region!r}")
    rate_pct = _RATES[region]

    discount = Decimal(str(discount_pct))
    if discount < 0 or discount > 100:
        raise ValueError(f"discount_pct must be between 0 and 100, got {discount_pct!r}")

    # Exact decimal arithmetic; quantize only at the end.
    base = Decimal(taxable_cents) * (Decimal(100) - discount) / Decimal(100)
    tax = base * rate_pct / Decimal(100)
    return int(tax.quantize(Decimal("1"), rounding=ROUND_HALF_UP))
