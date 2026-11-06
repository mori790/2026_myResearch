"""Tax module. Owned by agent2. Computes sales tax. The data files and rules are in data_tax/ next to this file.

Interface (committed decision tax_api):
    compute_tax(lines, region, discount_pct) -> int   (cents)
    tax_rate(region) -> Decimal   (percent, e.g. Decimal("8.25"))

Units: money is integer cents (1250 == $12.50); percentages are percent numbers (10 == 10%).
"""

import csv
import os
from decimal import Decimal, ROUND_HALF_UP

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_tax")


def _load_rates():
    """Return {region: tax_pct as Decimal} from data_tax/rates.csv."""
    path = os.path.join(_DATA_DIR, "rates.csv")
    rates = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            region = row["region"].strip()
            if region:
                rates[region] = Decimal(row["tax_pct"].strip())
    return rates


def _load_exempt_categories():
    """Return the set of exempt category names (lower-case) from data_tax/exempt_categories.csv."""
    path = os.path.join(_DATA_DIR, "exempt_categories.csv")
    exempt = set()
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            category = row["category"].strip().lower()
            if category:
                exempt.add(category)
    return exempt


_RATES = _load_rates()
_EXEMPT_CATEGORIES = _load_exempt_categories()


def tax_rate(region):
    """Return the sales tax percent for a region as a Decimal.

    region None means the customer has no region; it pays 0%.
    A region that is not in rates.csv raises KeyError.
    """
    if region is None:
        return Decimal("0")
    return _RATES[region.strip()]


def _is_exempt(category):
    return str(category).strip().lower() in _EXEMPT_CATEGORIES


def compute_tax(lines, region, discount_pct):
    """Return the sales tax for an order, in integer cents.

    lines        -- iterable of {"amount_cents": int, "category": str}
    region       -- customer region (e.g. "TX"), or None
    discount_pct -- customer discount in percent (10 means 10%)

    Rules (data_tax/RULES.md):
      taxable    = sum of amount_cents for lines whose category is not exempt
      base       = taxable * (100 - discount_pct) / 100
      tax        = base * tax_pct / 100, rounded to the cent (half up)
    An unknown region (not in rates.csv) or no region gives tax 0; no KeyError is raised.
    """
    taxable_cents = 0
    for line in lines:
        amount = line["amount_cents"]
        if isinstance(amount, bool) or not isinstance(amount, int):
            raise TypeError("amount_cents must be an int (cents), got %r" % (amount,))
        if not _is_exempt(line["category"]):
            taxable_cents += amount

    discount = Decimal(str(discount_pct))
    if discount < 0 or discount > 100:
        raise ValueError("discount_pct must be between 0 and 100, got %r" % (discount_pct,))

    if region is None or region.strip() not in _RATES:
        rate = Decimal("0")
    else:
        rate = _RATES[region.strip()]

    # Exact arithmetic: taxable * (100 - d) / 100 * rate / 100 == taxable * (100 - d) * rate / 10000
    exact_tax_cents = Decimal(taxable_cents) * (Decimal(100) - discount) * rate / Decimal(10000)
    return int(exact_tax_cents.quantize(Decimal("1"), rounding=ROUND_HALF_UP))
