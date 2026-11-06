"""Tax module. Owned by agent2. Computes sales tax. The data files and rules are in data_tax/ next to this file.

Committed interface (agreement topic tax_api v2):
    sales_tax(region, lines, discount_percent) -> {"tax_cents": int, "rate_percent": str}
      region            customer region string such as "TX" (from pricing get_customer), or None.
      lines             list of [sku, category, gross_line_cents] for known items, in invoice order.
      discount_percent  customer discount as a decimal string such as "10" or "8.25".
    Unknown region (including None) gives tax_cents 0 and rate_percent "0".
"""

import csv
import os
from decimal import Decimal, ROUND_HALF_UP

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_tax")
_HUNDRED = Decimal(100)


def _load_rates():
    rates = {}
    with open(os.path.join(_DATA_DIR, "rates.csv"), newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            region = row["region"].strip().upper()
            if region:
                rates[region] = Decimal(row["tax_pct"].strip())
    return rates


def _load_exempt_categories():
    exempt = set()
    with open(os.path.join(_DATA_DIR, "exempt_categories.csv"), newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            category = row["category"].strip().lower()
            if category:
                exempt.add(category)
    return exempt


_RATES = _load_rates()
_EXEMPT_CATEGORIES = _load_exempt_categories()


def _rate_for(region):
    """Tax percent (Decimal) for a region. Unknown or None means 0."""
    if region is None:
        return Decimal(0)
    return _RATES.get(str(region).strip().upper(), Decimal(0))


def tax_pct(region):
    """Tax percent for display only, e.g. Decimal('8.25') for TX."""
    return _rate_for(region)


def _is_exempt(category):
    return str(category).strip().lower() in _EXEMPT_CATEGORIES


def sales_tax(region, lines, discount_percent="0"):
    """Compute sales tax for one order. Returns {"tax_cents": int, "rate_percent": str}.

    Rules (data_tax/RULES.md):
      taxable = sum of gross_line_cents for lines whose category is not exempt
      base    = taxable * (100 - discount_percent) / 100     (exact Decimal)
      tax     = base * tax_pct / 100, rounded to whole cents, ROUND_HALF_UP
    """
    discount = Decimal(str(discount_percent).strip())
    if not (Decimal(0) <= discount <= _HUNDRED):
        raise ValueError("discount_percent must be between 0 and 100")

    taxable_cents = 0
    for line in lines:
        if len(line) != 3:
            raise ValueError("each line must be [sku, category, gross_line_cents]")
        _sku, category, gross_cents = line
        if not isinstance(gross_cents, int) or isinstance(gross_cents, bool):
            raise TypeError("gross_line_cents must be an int")
        if gross_cents < 0:
            raise ValueError("gross_line_cents must not be negative")
        if not _is_exempt(category):
            taxable_cents += gross_cents

    rate = _rate_for(region)
    if rate == 0:
        return {"tax_cents": 0, "rate_percent": "0"}

    base = Decimal(taxable_cents) * (_HUNDRED - discount) / _HUNDRED
    tax = (base * rate / _HUNDRED).quantize(Decimal(1), rounding=ROUND_HALF_UP)
    return {"tax_cents": int(tax), "rate_percent": str(rate)}
