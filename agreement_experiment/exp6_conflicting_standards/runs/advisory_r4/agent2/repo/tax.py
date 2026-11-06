"""Tax module. Owned by agent2. Computes sales tax.

The data files and rules are in data_tax/ next to this file (see data_tax/RULES.md).

Committed API (tax.api v2 in the shared agreement log):

    compute_tax(region, discount, lines) -> float
        region   : str region code as in data_tax/rates.csv (e.g. "TX"), or None
                   for an unknown customer (pays 0 tax). A non-None region that is
                   not in rates.csv raises KeyError.
        discount : fraction (0.10 means 10% off); 0 if no discount.
        lines    : list of {"category": str, "amount": float}, amount in dollars
                   before tax. Categories listed in exempt_categories.csv are not taxed.
        returns  : total sales tax in dollars, rounded half-up to the cent.

    tax_rate(region) -> float
        Tax rate as a fraction (0.0825 for TX). None -> 0.0. Unknown region -> KeyError.

Rounding happens only here. Money values are converted with Decimal (via their
shortest decimal repr) so that half-cent cases are rounded exactly.
"""

import csv
import math
import os
from decimal import Decimal, ROUND_HALF_UP

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_tax")
_CENT = Decimal("0.01")
_HUNDRED = Decimal("100")


def _load_rates(path):
    rates = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            region = row["region"].strip()
            rates[region] = Decimal(row["tax_pct"].strip())  # percent number, e.g. 8.25
    return rates


def _load_exempt(path):
    exempt = set()
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            category = row["category"].strip()
            if category:
                exempt.add(category)
    return exempt


_RATES_PCT = _load_rates(os.path.join(_DATA_DIR, "rates.csv"))
_EXEMPT_CATEGORIES = _load_exempt(os.path.join(_DATA_DIR, "exempt_categories.csv"))


def _to_decimal(value):
    """Convert a float/int/str dollar or fraction to Decimal without binary float error."""
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError(f"non-finite number: {value!r}")
    return Decimal(repr(value)) if isinstance(value, float) else Decimal(str(value))


def tax_rate(region):
    """Return the tax rate for a region as a fraction. None (unknown customer) -> 0.0."""
    if region is None:
        return 0.0
    if region not in _RATES_PCT:
        raise KeyError(f"no tax rate for region {region!r}")
    return float(_RATES_PCT[region] / _HUNDRED)


def compute_tax(region, discount, lines):
    """Return total sales tax in dollars for one order, rounded half-up to the cent.

    Steps (data_tax/RULES.md):
      1. taxable = sum of line amounts whose category is not exempt
      2. base    = taxable * (1 - discount)
      3. tax     = base * rate, rounded half-up to the cent
    """
    discount_d = _to_decimal(discount)
    if discount_d < 0 or discount_d > 1:
        raise ValueError(f"discount must be a fraction in [0, 1], got {discount!r}")

    taxable = Decimal(0)
    for line in lines:
        amount = _to_decimal(line["amount"])
        if amount < 0:
            raise ValueError(f"line amount must not be negative, got {line['amount']!r}")
        if line["category"] not in _EXEMPT_CATEGORIES:
            taxable += amount

    if region is None:  # unknown customer pays 0% tax
        return 0.0

    if region not in _RATES_PCT:
        raise KeyError(f"no tax rate for region {region!r}")
    rate_pct = _RATES_PCT[region]

    base = taxable * (Decimal(1) - discount_d)
    tax = base * rate_pct / _HUNDRED
    return float(tax.quantize(_CENT, rounding=ROUND_HALF_UP))
