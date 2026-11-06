"""Tax module. Owned by agent2. Computes sales tax.

The data files and rules are in data_tax/ next to this file:
  - rates.csv              region -> tax percent (Decimal)
  - exempt_categories.csv  item categories that are not taxed
  - RULES.md               the tax rules implemented here

Agreed interface (decision `tax_interface`, committed):

    calculate_tax(region, lines, discount_pct) -> (tax_cents, tax_percent)

  region        : two-letter US state code from pricing (e.g. "TX"), or None.
                  None or a region not in rates.csv means 0% tax.
  lines         : iterable of (category, amount_cents) for EVERY line item of the
                  order. amount_cents = unit price * quantity, UNDISCOUNTED.
                  category is a str, or None (treated as not exempt).
  discount_pct  : Decimal (or int) percent, 0..100. None means 0.

All money is integer cents. All percentages are decimal.Decimal.
"""

import csv
import os
from decimal import Decimal, ROUND_HALF_UP

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_tax")
_RATES_PATH = os.path.join(_DATA_DIR, "rates.csv")
_EXEMPT_PATH = os.path.join(_DATA_DIR, "exempt_categories.csv")

_ZERO_PERCENT = Decimal("0")
_HUNDRED = Decimal("100")


def _normalize_category(category):
    return category.strip().lower()


def _load_rates(path=_RATES_PATH):
    """Return {region: Decimal tax percent}."""
    rates = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            region = row["region"].strip().upper()
            rates[region] = Decimal(row["tax_pct"].strip())
    return rates


def _load_exempt_categories(path=_EXEMPT_PATH):
    """Return the set of exempt categories, normalized to lowercase."""
    exempt = set()
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            category = row["category"].strip()
            if category:
                exempt.add(_normalize_category(category))
    return frozenset(exempt)


_RATES = _load_rates()
_EXEMPT_CATEGORIES = _load_exempt_categories()


def tax_percent_for_region(region):
    """Tax percent (Decimal) for a region. Unknown or None region -> 0."""
    if region is None:
        return _ZERO_PERCENT
    return _RATES.get(region.strip().upper(), _ZERO_PERCENT)


def is_exempt(category):
    """True if the category is listed in exempt_categories.csv."""
    if category is None:
        return False
    return _normalize_category(category) in _EXEMPT_CATEGORIES


def _to_percent(value):
    if value is None:
        return _ZERO_PERCENT
    if isinstance(value, Decimal):
        percent = value
    elif isinstance(value, int) and not isinstance(value, bool):
        percent = Decimal(value)
    else:
        raise TypeError(f"discount_pct must be Decimal, int or None, got {type(value).__name__}")
    if not (_ZERO_PERCENT <= percent <= _HUNDRED):
        raise ValueError(f"discount_pct must be between 0 and 100, got {percent}")
    return percent


def calculate_tax(region, lines, discount_pct):
    """Compute sales tax for an order.

    Steps (RULES.md):
      1. Drop lines whose category is exempt.
      2. taxable_cents = sum of the remaining line amounts.
      3. base = taxable_cents * (100 - discount_pct) / 100   (exact Decimal)
      4. tax  = base * tax_pct / 100, rounded once, half up, to the cent.

    Returns (tax_cents: int, tax_percent: Decimal).
    """
    tax_pct = tax_percent_for_region(region)
    discount = _to_percent(discount_pct)

    taxable_cents = 0
    for category, amount_cents in lines:
        if not isinstance(amount_cents, int) or isinstance(amount_cents, bool):
            raise TypeError(f"amount_cents must be int, got {type(amount_cents).__name__}")
        if amount_cents < 0:
            raise ValueError(f"amount_cents must be non-negative, got {amount_cents}")
        if not is_exempt(category):
            taxable_cents += amount_cents

    if tax_pct == _ZERO_PERCENT or taxable_cents == 0:
        return 0, tax_pct

    # Exact arithmetic: taxable * (100 - d) * pct / (100 * 100).
    numerator = Decimal(taxable_cents) * (_HUNDRED - discount) * tax_pct
    tax = (numerator / Decimal(10000)).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    return int(tax), tax_pct
