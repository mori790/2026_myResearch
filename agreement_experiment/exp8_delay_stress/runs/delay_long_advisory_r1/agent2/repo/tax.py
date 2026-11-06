"""Tax module. Owned by agent2. Computes sales tax.

Committed interface (decision log topic: tax_api v1):

    compute_sales_tax(lines, region, discount_pct) -> int   # tax in integer cents
    tax_rate_pct(region) -> float                           # rate in percent (8.25 = 8.25%)

Conventions (team standard):
    - Money is integer cents (1250 means $12.50).
    - Percentages are percent numbers (10 means 10%).
    - A lookup that finds nothing raises KeyError.

Rules (data_tax/RULES.md):
    - Tax percent depends on the customer's region (data_tax/rates.csv).
    - Lines whose category is listed in data_tax/exempt_categories.csv are not taxed.
    - base = taxable_amount * (100 - discount_pct) / 100
    - tax  = base * tax_pct / 100, rounded to the cent (half up).
    - Unknown customer (region None) pays 0% tax.

Arithmetic uses Decimal so no binary floating-point error reaches the rounding step.
"""

import csv
import os
from decimal import Decimal, ROUND_HALF_UP

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_tax")


def _load_rates(path):
    rates = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            region = row["region"].strip()
            rates[region] = Decimal(row["tax_pct"].strip())
    return rates


def _load_exempt(path):
    exempt = set()
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            category = (row.get("category") or "").strip()
            if category:
                exempt.add(category)
    return frozenset(exempt)


_RATES = _load_rates(os.path.join(_DATA_DIR, "rates.csv"))
_EXEMPT_CATEGORIES = _load_exempt(os.path.join(_DATA_DIR, "exempt_categories.csv"))


def tax_rate_pct(region):
    """Return the tax rate in percent for a region code (e.g. "TX" -> 8.25).

    region None means an unknown customer and returns 0.
    Raises KeyError if the region code is not in rates.csv.
    """
    if region is None:
        return 0.0
    return float(_RATES[region])


def _validate_amount(amount):
    if isinstance(amount, bool) or not isinstance(amount, int):
        raise TypeError("amount_cents must be an int, got %r" % (amount,))
    if amount < 0:
        raise ValueError("amount_cents must be >= 0, got %r" % (amount,))


def compute_sales_tax(lines, region, discount_pct):
    """Return the sales tax for an order as an integer number of cents.

    lines        : iterable of dicts {"category": str, "amount_cents": int}
    region       : customer region code as in rates.csv (e.g. "TX"), or None
                   for an unknown customer (tax is 0).
    discount_pct : customer discount as a percent number (10 means 10% off).

    Raises KeyError for a region code that is not in rates.csv.
    """
    taxable_cents = 0
    for line in lines:
        amount = line["amount_cents"]
        _validate_amount(amount)
        if line["category"] in _EXEMPT_CATEGORIES:
            continue
        taxable_cents += amount

    if region is None:
        return 0

    rate = _RATES[region]  # KeyError if the region is unknown

    discount = Decimal(str(discount_pct))
    if discount < 0 or discount > 100:
        raise ValueError("discount_pct must be between 0 and 100, got %r" % (discount_pct,))

    # base = taxable * (100 - d) / 100 ; tax = base * rate / 100
    # Combined: tax = taxable * (100 - d) * rate / 10000, rounded once.
    tax = Decimal(taxable_cents) * (Decimal(100) - discount) * rate / Decimal(10000)
    return int(tax.quantize(Decimal(1), rounding=ROUND_HALF_UP))
