"""Tax module. Owned by agent2. Computes sales tax.

The data files and rules are in data_tax/ next to this file.

Agreed API (agree.py topic ``tax_api`` v3, committed):

    get_tax(region, discount_rate, lines) -> (Decimal tax_rate, Decimal tax_amount)

    region        str from the customer dict (e.g. "TX"), or None for an
                  unknown customer (-> 0% tax).
    discount_rate Decimal fraction from the customer dict (0.10 = 10% off).
    lines         iterable of (category, amount) with UNdiscounted line
                  amounts as Decimal dollars (e.g. Decimal("12.50")).

Other committed conventions used here:
    money_unit v2    : Decimal dollars; quantized to 0.01 only for the final tax.
    percent_unit v1  : fractions (10% is 0.10); rates.csv stores percent
                       numbers, so they are divided by 100 on load.
    lookup_miss v1   : unknown customer -> None (handled by returning 0 tax).

Rules (data_tax/RULES.md):
    taxable  = sum of line amounts whose category is NOT in exempt_categories.csv
    base     = taxable * (1 - discount_rate)
    tax      = base * tax_rate, rounded to the cent (half up)
    unknown customer pays 0%
"""

import csv
import os
from decimal import Decimal, ROUND_HALF_UP

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_tax")
_CENT = Decimal("0.01")
_ZERO_RATE = Decimal("0")
_ZERO_TAX = Decimal("0.00")


def _load_rates():
    """Return {region: Decimal fraction}, e.g. {"TX": Decimal("0.0825")}."""
    rates = {}
    path = os.path.join(_DATA_DIR, "rates.csv")
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            region = row["region"].strip()
            # rates.csv is in percent numbers (8.25); convert to a fraction.
            rates[region] = Decimal(row["tax_pct"].strip()) / Decimal("100")
    return rates


def _load_exempt_categories():
    """Return the set of exempt category names (normalized to lower case)."""
    exempt = set()
    path = os.path.join(_DATA_DIR, "exempt_categories.csv")
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            name = (row.get("category") or "").strip().lower()
            if name:
                exempt.add(name)
    return exempt


_RATES = _load_rates()
_EXEMPT_CATEGORIES = _load_exempt_categories()


def _to_decimal(value):
    """Accept Decimal, int, or str as money/percent values without float error."""
    if isinstance(value, Decimal):
        return value
    if isinstance(value, float):
        # Go through repr so 0.1 becomes Decimal("0.1") rather than the binary value.
        return Decimal(repr(value))
    return Decimal(str(value))


def get_tax_rate(region):
    """Return the tax rate as a Decimal fraction for a region.

    None (unknown customer) -> 0. A region code not present in rates.csv
    raises KeyError, following the team's lookup convention for tables that
    tax.py itself owns.
    """
    if region is None:
        return _ZERO_RATE
    return _RATES[region.strip()]


def is_exempt(category):
    """True if items in this category are not taxed."""
    return str(category).strip().lower() in _EXEMPT_CATEGORIES


def get_tax(region, discount_rate, lines):
    """Compute sales tax for one order.

    Returns (tax_rate, tax_amount): tax_rate is a Decimal fraction and
    tax_amount is Decimal dollars quantized to 0.01 (half up).
    """
    tax_rate = get_tax_rate(region)

    discount = _to_decimal(discount_rate)
    if not (Decimal("0") <= discount <= Decimal("1")):
        raise ValueError(f"discount_rate must be a fraction in [0, 1], got {discount_rate!r}")

    taxable = Decimal("0")
    for category, amount in lines:
        if not is_exempt(category):
            taxable += _to_decimal(amount)

    if region is None or tax_rate == 0 or taxable == 0:
        # Unknown customer, zero-rate region, or nothing taxable.
        return tax_rate, _ZERO_TAX

    base = taxable * (Decimal("1") - discount)
    tax = (base * tax_rate).quantize(_CENT, rounding=ROUND_HALF_UP)
    return tax_rate, tax
