"""Tax module. Owned by agent2. Computes sales tax.

Committed team decisions (see the shared agreement log):
  - tax.money_unit: all money amounts are integer cents (1250 = $12.50).
  - tax.interface: compute_tax(region, lines, discount_pct) -> int cents,
    where lines = [(category, amount_cents), ...] and percent values are
    percent numbers (10 means 10%).
  - tax.unknown_region: an unknown region raises KeyError; region=None
    means no region is known and the tax is 0.
  - pricing_api v3: customer_region(customer_id) returns None for an
    unknown customer, and the caller passes that None here.

Data files live in data_tax/ next to this module:
  - rates.csv:              region,tax_pct
  - exempt_categories.csv:  category
  - RULES.md:               the tax rules (summarized in this module)

Tax rule (RULES.md):
  base = taxable_amount * (100 - discount_pct) / 100
  tax  = round_half_up(base * tax_pct / 100)   (to the whole cent)
"""

import csv
import os
from decimal import ROUND_HALF_UP, Decimal

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_tax")
_HUNDRED = Decimal(100)


def _load_rates():
    """Return {region: Decimal(tax_pct)} read from rates.csv."""
    rates = {}
    path = os.path.join(_DATA_DIR, "rates.csv")
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            region = row["region"].strip()
            # Decimal from the string keeps values such as 8.875 exact.
            rates[region] = Decimal(row["tax_pct"].strip())
    return rates


def _load_exempt_categories():
    """Return the set of category names listed in exempt_categories.csv."""
    exempt = set()
    path = os.path.join(_DATA_DIR, "exempt_categories.csv")
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            category = (row.get("category") or "").strip()
            if category:
                exempt.add(category)
    return exempt


_RATES = _load_rates()
_EXEMPT = _load_exempt_categories()


def tax_pct(region):
    """Return the tax percent for `region` as a Decimal (e.g. 8.25 for 8.25%).

    Raises KeyError if the region is not listed in rates.csv.
    """
    try:
        return _RATES[region]
    except KeyError:
        raise KeyError(f"no tax rate for region {region!r}") from None


def is_exempt(category):
    """Return True if items of `category` are not taxed (exempt_categories.csv)."""
    return category in _EXEMPT


def _to_decimal(value):
    """Convert a percent number (int, float, str or Decimal) to Decimal exactly."""
    if isinstance(value, Decimal):
        return value
    if isinstance(value, float):
        # str() gives the shortest repr, avoiding binary float noise.
        return Decimal(str(value))
    if isinstance(value, (int, str)) and not isinstance(value, bool):
        return Decimal(value)
    raise TypeError(f"percent must be int, float, str or Decimal, got {type(value).__name__}")


def compute_tax(region, lines, discount_pct=0):
    """Return the sales tax for an order in integer cents.

    region       -- customer's region code (e.g. "TX"), or None if no region
                    is known (tax is 0).
    lines        -- iterable of (category, amount_cents) pairs. Amounts are
                    integer cents. Lines whose category is exempt are not taxed.
    discount_pct -- customer's discount as a percent number (10 means 10%).
                    Use 0 for no discount.

    Raises KeyError if `region` is not in rates.csv.
    """
    lines = list(lines)
    for category, amount in lines:
        if not isinstance(amount, int) or isinstance(amount, bool):
            raise TypeError(f"amount_cents must be int, got {type(amount).__name__}")

    if region is None:
        return 0

    rate = tax_pct(region)
    taxable_total = sum(amount for category, amount in lines if not is_exempt(category))

    discount = _to_decimal(discount_pct)
    base = Decimal(taxable_total) * (_HUNDRED - discount) / _HUNDRED
    tax = base * rate / _HUNDRED
    return int(tax.quantize(Decimal(1), rounding=ROUND_HALF_UP))
