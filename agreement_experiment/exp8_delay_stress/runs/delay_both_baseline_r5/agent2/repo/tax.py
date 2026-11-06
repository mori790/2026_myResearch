"""Tax module. Owned by agent2. Computes sales tax. The data files and rules are in data_tax/ next to this file.

Public API (money in integer cents, percentages as percent numbers):

    tax_rate_pct(region)                      -> float
    is_exempt(category)                       -> bool
    sales_tax_cents(lines, region, discount_pct=0) -> int

Rules (data_tax/RULES.md):
    * The tax percent depends on the customer's region (rates.csv).
    * Items whose category is listed in exempt_categories.csv are not taxed.
    * base = taxable_amount * (100 - discount_pct) / 100
    * tax  = base * tax_pct / 100, rounded to the cent (half up).
    * An unknown customer (region is None) pays 0% tax.
"""

import csv
import os
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_tax")
_RATES_PATH = os.path.join(_DATA_DIR, "rates.csv")
_EXEMPT_PATH = os.path.join(_DATA_DIR, "exempt_categories.csv")


def _normalize(name):
    return str(name).strip().lower()


def _load_rates(path):
    rates = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            region = _normalize(row["region"])
            rates[region] = Decimal(row["tax_pct"].strip())
    return rates


def _load_exempt(path):
    exempt = set()
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            category = _normalize(row["category"])
            if category:
                exempt.add(category)
    return frozenset(exempt)


_RATES = _load_rates(_RATES_PATH)
_EXEMPT = _load_exempt(_EXEMPT_PATH)


def _rate_decimal(region):
    if region is None:
        return Decimal(0)
    key = _normalize(region)
    if key not in _RATES:
        raise KeyError(f"no tax rate for region {region!r}")
    return _RATES[key]


def tax_rate_pct(region):
    """Return the sales tax percent for a customer region.

    region=None means an unknown customer, which pays 0%.
    An unknown region string raises KeyError.
    """
    return float(_rate_decimal(region))


def is_exempt(category):
    """Return True if items in this category are not taxed."""
    return _normalize(category) in _EXEMPT


def sales_tax_cents(lines, region, discount_pct=0):
    """Return the sales tax for an order, in integer cents.

    lines        : iterable of (category, amount_cents) tuples, where
                   amount_cents = quantity * unit price in cents, before
                   discount and tax. Exempt categories are excluded from
                   the taxable amount.
    region       : customer's region (e.g. "TX"), or None for an unknown
                   customer (0% tax). An unknown region raises KeyError.
    discount_pct : customer's discount in percent (e.g. 10 for 10%).

    The computation uses exact decimal arithmetic and rounds once, at the
    end, to the nearest cent (half up).
    """
    taxable = 0
    for category, amount_cents in lines:
        if not is_exempt(category):
            taxable += int(amount_cents)

    try:
        discount = Decimal(str(discount_pct))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"invalid discount_pct {discount_pct!r}") from exc
    if discount < 0 or discount > 100:
        raise ValueError(f"discount_pct must be between 0 and 100, got {discount_pct!r}")

    rate_pct = _rate_decimal(region)

    # base = taxable * (100 - discount) / 100
    # tax  = base * rate / 100 = taxable * (100 - discount) * rate / 10000
    tax = Decimal(taxable) * (Decimal(100) - discount) * rate_pct / Decimal(10000)
    return int(tax.quantize(Decimal("1"), rounding=ROUND_HALF_UP))
