"""Tax module. Owned by agent2. Computes sales tax.

The data files and rules are in data_tax/ next to this file.

Agreed API (decision topic ``tax_api`` v2 in the shared log):

    compute_tax(customer_region, lines, discount_pct) -> int
        Tax in integer cents.
    tax_percent(customer_region) -> float
        Tax percent number for the region (8.25 means 8.25%).

Conventions (team standard):
    * Money amounts are integer cents (1250 means $12.50).
    * Percentages are percent numbers (10 means 10%, 8.25 means 8.25%).
    * A lookup that finds nothing raises KeyError.
    * An unknown customer (region is None) pays 0% tax.
"""

import csv
import os
from decimal import Decimal, ROUND_HALF_UP

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_tax")
_RATES_PATH = os.path.join(_DATA_DIR, "rates.csv")
_EXEMPT_PATH = os.path.join(_DATA_DIR, "exempt_categories.csv")


def _load_rates(path=_RATES_PATH):
    """Return {region: tax_pct as Decimal} from rates.csv."""
    rates = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            region = row["region"].strip()
            rates[region] = Decimal(row["tax_pct"].strip())
    return rates


def _load_exempt_categories(path=_EXEMPT_PATH):
    """Return the set of category names that are not taxed."""
    exempt = set()
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            category = (row.get("category") or "").strip()
            if category:
                exempt.add(category)
    return exempt


_RATES = _load_rates()
_EXEMPT_CATEGORIES = _load_exempt_categories()


def tax_percent(customer_region):
    """Return the tax percent number for a region (e.g. 8.25 for TX).

    ``None`` (unknown customer) gives 0. A region that is not in rates.csv
    raises KeyError.
    """
    if customer_region is None:
        return 0.0
    if customer_region not in _RATES:
        raise KeyError(f"no tax rate for region {customer_region!r}")
    return float(_RATES[customer_region])


def compute_tax(customer_region, lines, discount_pct):
    """Return the sales tax for an order, in integer cents.

    Args:
        customer_region: region code as in rates.csv (e.g. "TX"), or None
            for an unknown customer (tax 0). An unknown non-None region
            raises KeyError.
        lines: iterable of dicts with keys "category" (str) and
            "amount_cents" (int, line total before discount and tax).
            Lines whose category is in exempt_categories.csv are not taxed.
        discount_pct: customer discount as a percent number (10 means 10%).
            Use 0 if there is no discount.

    Returns:
        int: tax in cents, computed as
        round_half_up(taxable * (100 - discount_pct) * tax_pct / 10000),
        using exact decimal arithmetic and rounding once at the end.
    """
    if customer_region is None:
        return 0
    if customer_region not in _RATES:
        raise KeyError(f"no tax rate for region {customer_region!r}")

    taxable = 0
    for line in lines:
        if line["category"] in _EXEMPT_CATEGORIES:
            continue
        amount = line["amount_cents"]
        if not isinstance(amount, int) or isinstance(amount, bool):
            raise TypeError("amount_cents must be an int (cents)")
        taxable += amount

    discount = Decimal(str(discount_pct))
    if discount < 0 or discount > 100:
        raise ValueError("discount_pct must be between 0 and 100")

    # base = taxable * (100 - discount) / 100 ; tax = base * tax_pct / 100
    # tax_cents = taxable * (100 - discount) * tax_pct / 10000
    raw = (Decimal(taxable) * (Decimal(100) - discount) * _RATES[customer_region]
           / Decimal(10000))
    return int(raw.quantize(Decimal("1"), rounding=ROUND_HALF_UP))
