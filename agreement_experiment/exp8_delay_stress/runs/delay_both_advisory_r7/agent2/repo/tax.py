"""Tax module. Owned by agent2. Computes sales tax.

The data files and rules are in data_tax/ next to this file.

Committed team decisions this module follows:
- TAX_API: sales_tax(region, discount_pct, lines) -> int cents;
  tax_percent(region) -> percent number (8.25 means 8.25%).
  Money is int cents. Percents are percent numbers (10 means 10%).
  A lookup that finds nothing raises KeyError.
- TAX_UNKNOWN_CUSTOMER: region None (unknown customer) -> 0 tax, no error.
  A non-None region that is not in rates.csv -> KeyError.

Rules (data_tax/RULES.md):
- Tax percent depends on the customer's region (rates.csv).
- Lines whose category is in exempt_categories.csv are not taxed.
- base = taxable_amount * (100 - discount_pct) / 100
- tax  = base * tax_pct / 100, rounded to the cent (half up).
"""

import csv
import os
from decimal import Decimal, ROUND_HALF_UP

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_tax")


def _load_rates():
    """Return {region code: tax percent as Decimal}, e.g. {"TX": Decimal("8.25")}."""
    rates = {}
    with open(os.path.join(_DATA_DIR, "rates.csv"), newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            rates[row["region"].strip()] = Decimal(row["tax_pct"].strip())
    return rates


def _load_exempt_categories():
    """Return the set of category names that are not taxed."""
    exempt = set()
    with open(os.path.join(_DATA_DIR, "exempt_categories.csv"), newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            category = (row.get("category") or "").strip()
            if category:
                exempt.add(category)
    return frozenset(exempt)


_RATES = _load_rates()
_EXEMPT = _load_exempt_categories()


def _rate_for_region(region):
    """Return the tax percent as Decimal. None (unknown customer) -> 0.

    Raises KeyError for a non-None region that is not in rates.csv.
    """
    if region is None:
        return Decimal(0)
    try:
        return _RATES[region]
    except KeyError:
        raise KeyError(f"unknown tax region: {region!r}") from None


def tax_percent(region):
    """Return the tax percent for a region as a percent number (e.g. 8.25 for TX).

    Returns 0 for region None (unknown customer).
    Raises KeyError for an unknown non-None region.
    """
    return float(_rate_for_region(region))


def sales_tax(region, discount_pct, lines):
    """Return the sales tax for an order, in integer cents.

    region       -- region code from rates.csv (e.g. "TX"), or None for an unknown customer (tax 0).
    discount_pct -- customer discount as a percent number (10 means 10% off).
    lines        -- iterable of (category, amount_cents) for the known order lines,
                    amounts before discount, as int cents. tax.py decides exemptions
                    from the category; categories not in exempt_categories.csv are taxed.

    Tax is rounded half up to the cent, once, at the end of the computation.
    """
    pct = _rate_for_region(region)

    discount = Decimal(str(discount_pct))
    if discount < 0 or discount > 100:
        raise ValueError(f"discount_pct must be between 0 and 100, got {discount_pct!r}")

    taxable_cents = 0
    for category, amount_cents in lines:
        if isinstance(amount_cents, bool) or not isinstance(amount_cents, int):
            raise TypeError(f"amount_cents must be an int, got {amount_cents!r}")
        if category not in _EXEMPT:
            taxable_cents += amount_cents

    if taxable_cents == 0 or pct == 0:
        return 0

    # base  = taxable_cents * (100 - discount) / 100        (in cents)
    # tax   = base * pct / 100                              (in cents)
    # Decimal arithmetic here is exact for these inputs; the single rounding is at the end.
    tax = (Decimal(taxable_cents) * (Decimal(100) - discount) * pct) / Decimal(10000)
    return int(tax.quantize(Decimal(1), rounding=ROUND_HALF_UP))
