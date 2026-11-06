"""Tax module. Owned by agent2. Computes sales tax.

The data files and rules are in data_tax/ next to this file:
  - data_tax/rates.csv             region -> tax percent
  - data_tax/exempt_categories.csv categories that are not taxed
  - data_tax/RULES.md              the tax rules

Units (team standard):
  - money:   integer cents (1250 means $12.50)
  - percent: percent numbers (10 means 10%, 8.25 means 8.25%)

Rules implemented (see data_tax/RULES.md):
  - tax percent depends on the customer's region
  - items whose category is exempt are not taxed
  - base = taxable_amount * (100 - discount_pct) / 100
  - tax  = base * tax_pct / 100, rounded to the cent (half up)
  - an unknown customer (region None) pays 0% tax
"""

import csv
import os
from decimal import Decimal, ROUND_HALF_UP

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_tax")


def _load_rates():
    rates = {}
    path = os.path.join(_DATA_DIR, "rates.csv")
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            region = row["region"].strip()
            if region:
                # Decimal from the string keeps the value exact (8.875 stays 8.875).
                rates[region] = Decimal(row["tax_pct"].strip())
    return rates


def _load_exempt_categories():
    categories = set()
    path = os.path.join(_DATA_DIR, "exempt_categories.csv")
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            category = row["category"].strip()
            if category:
                categories.add(category)
    return frozenset(categories)


_RATES = _load_rates()
_EXEMPT_CATEGORIES = _load_exempt_categories()


def tax_rate_pct(region):
    """Return the sales tax percent for a region, e.g. 'TX' -> 8.25.

    Raises KeyError if the region is not in rates.csv.
    """
    return float(_RATES[region])


def is_taxable(category):
    """Return True if items of this category are taxed (i.e. not exempt)."""
    return category not in _EXEMPT_CATEGORIES


def _check_cents(value, name):
    # bool is a subclass of int, so exclude it explicitly.
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be an int number of cents, got {value!r}")
    if value < 0:
        raise ValueError(f"{name} must not be negative, got {value}")


def compute_tax(lines, region, discount_pct=0):
    """Compute sales tax for one order.

    lines:        iterable of dicts with
                    'amount_cents' (int): line total in cents (already multiplied by quantity)
                    'category'     (str): item category, used for the exemption check
    region:       the customer's region (e.g. 'TX'), or None for an unknown customer
                  (an unknown customer pays 0% tax).
                  An unknown region string raises KeyError.
    discount_pct: the customer's discount in percent numbers (e.g. 10 for 10%).
                  Use 0 when the customer has no discount.

    Returns a dict:
        'taxable_cents': int   sum of the taxable line amounts, before discount
        'rate_pct':      float tax percent applied (0.0 for an unknown customer)
        'tax_cents':     int   tax amount in cents, rounded half up

    Raises TypeError for non-int amounts (e.g. float dollars), ValueError for
    negative amounts or a discount outside 0..100, and KeyError for an unknown region.
    """
    taxable_cents = 0
    for line in lines:
        amount = line["amount_cents"]
        _check_cents(amount, "amount_cents")
        if is_taxable(line["category"]):
            taxable_cents += amount

    if isinstance(discount_pct, bool) or not isinstance(discount_pct, (int, float, Decimal)):
        raise TypeError(f"discount_pct must be a number of percent, got {discount_pct!r}")
    discount = Decimal(str(discount_pct))
    if discount < 0 or discount > 100:
        raise ValueError(f"discount_pct must be between 0 and 100, got {discount_pct}")

    if region is None:
        rate = Decimal(0)  # unknown customer pays no tax
    else:
        rate = _RATES[region]  # KeyError for an unknown region

    # Exact decimal arithmetic; round only once, at the end, half up.
    base = Decimal(taxable_cents) * (Decimal(100) - discount) / Decimal(100)
    tax = base * rate / Decimal(100)
    tax_cents = int(tax.quantize(Decimal(1), rounding=ROUND_HALF_UP))

    return {
        "taxable_cents": taxable_cents,
        "rate_pct": float(rate),
        "tax_cents": tax_cents,
    }
