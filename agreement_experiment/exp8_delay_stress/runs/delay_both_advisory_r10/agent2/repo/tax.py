"""Tax module. Owned by agent2. Computes sales tax.

The data files and rules are in data_tax/ next to this file:
  - data_tax/rates.csv              region -> tax percent (percent numbers, 8.25 = 8.25%)
  - data_tax/exempt_categories.csv  item categories that are not taxed
  - data_tax/RULES.md               the tax rules

Team decisions this module follows (see the shared agreement log):
  - money-units:  all money amounts are integer cents (1250 = $12.50).
  - percent-units: all percentages are percent numbers (10 = 10%).
  - tax-api: compute_tax(region, lines, discount_pct=0) -> int cents.
  - unknown-customer-and-rounding: region None (unknown customer) pays 0 tax;
    an unknown region string raises KeyError; exact arithmetic, and only the
    final tax is rounded to the cent (ROUND_HALF_UP).

Rules (data_tax/RULES.md):
  taxable_amount = sum of line amounts whose category is NOT exempt
  base           = taxable_amount * (100 - discount_pct) / 100
  tax            = base * tax_pct / 100, rounded to the cent (half up)
"""

import csv
import os
from decimal import Decimal, ROUND_HALF_UP

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_tax")
_RATES_PATH = os.path.join(_DATA_DIR, "rates.csv")
_EXEMPT_PATH = os.path.join(_DATA_DIR, "exempt_categories.csv")


def _load_rates(path):
    """Return {region: Decimal tax percent} from rates.csv."""
    rates = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            region = row["region"].strip()
            rates[region] = Decimal(row["tax_pct"].strip())
    return rates


def _load_exempt(path):
    """Return the set of exempt category names from exempt_categories.csv."""
    exempt = set()
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            category = row["category"].strip()
            if category:
                exempt.add(category)
    return exempt


_RATES = _load_rates(_RATES_PATH)
_EXEMPT_CATEGORIES = _load_exempt(_EXEMPT_PATH)


def _to_decimal(value):
    """Convert a number (int, float, str or Decimal) to Decimal without float artifacts."""
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def tax_rate(region):
    """Return the tax rate for a customer region, as a percent number (Decimal).

    region None means an unknown customer, who pays 0% tax.
    An unknown region string raises KeyError.
    """
    if region is None:
        return Decimal("0")
    if region not in _RATES:
        raise KeyError(f"no tax rate for region {region!r}")
    return _RATES[region]


def is_exempt(category):
    """Return True if items in this category are not taxed."""
    return category in _EXEMPT_CATEGORIES


def compute_tax(region, lines, discount_pct=0):
    """Return the sales tax for an order, in integer cents.

    region       : customer region code (e.g. "TX"), or None for an unknown customer.
    lines        : iterable of (category, amount_cents) pairs, one per order line,
                   with GROSS amounts (before the customer discount).
    discount_pct : customer discount in percent numbers (10 = 10% off).

    The discount is applied here, to the taxable amount only:
        base = taxable_cents * (100 - discount_pct) / 100
        tax  = base * tax_pct / 100, rounded to the nearest cent (half up).
    """
    rate = tax_rate(region)

    taxable_cents = 0
    for category, amount_cents in lines:
        if not is_exempt(category):
            taxable_cents += amount_cents

    discount = _to_decimal(discount_pct)
    base = Decimal(taxable_cents) * (Decimal("100") - discount) / Decimal("100")
    tax = base * rate / Decimal("100")
    return int(tax.quantize(Decimal("1"), rounding=ROUND_HALF_UP))
