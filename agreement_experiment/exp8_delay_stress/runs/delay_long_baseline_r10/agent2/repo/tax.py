"""Tax module. Owned by agent2. Computes sales tax. The data files and rules are in data_tax/ next to this file.

Conventions (team standard):
- Money amounts are integers in cents (1250 means $12.50).
- Percentages are percent numbers (10% is 10, 8.25% is 8.25).
- A lookup that finds nothing raises KeyError.

Public API (agreed in topic `tax_api`):
- compute_tax(lines, region, discount_pct=0) -> int   (sales tax in cents)
- get_rate(region) -> Decimal                          (tax percent for a region)
- is_exempt(category) -> bool

Rules (data_tax/RULES.md):
- Tax percent depends on the customer's region (rates.csv).
- Items whose category is listed in exempt_categories.csv are not taxed.
- base = taxable_amount * (100 - discount_pct) / 100
- tax  = base * tax_pct / 100, rounded to the cent (half up).
- An unknown customer (region is None) pays 0% tax.
"""

import csv
import os
from decimal import Decimal, ROUND_HALF_UP

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_tax")
_RATES_PATH = os.path.join(_DATA_DIR, "rates.csv")
_EXEMPT_PATH = os.path.join(_DATA_DIR, "exempt_categories.csv")


def _load_rates(path):
    rates = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            region = row["region"].strip()
            rates[region] = Decimal(row["tax_pct"].strip())
    return rates


def _load_exempt(path):
    with open(path, newline="", encoding="utf-8") as f:
        return {row["category"].strip() for row in csv.DictReader(f) if row["category"].strip()}


_RATES = _load_rates(_RATES_PATH)
_EXEMPT = _load_exempt(_EXEMPT_PATH)


def _to_decimal(value):
    # Go through str() so that floats such as 8.25 become exact decimals "8.25".
    return Decimal(str(value))


def get_rate(region):
    """Return the sales tax percent for `region` as a Decimal (e.g. Decimal('8.25')).

    region=None means an unknown customer and returns 0.
    Raises KeyError if a region string is not in rates.csv.
    """
    if region is None:
        return Decimal(0)
    return _RATES[region]


def is_exempt(category):
    """True if items of this category are not taxed (listed in exempt_categories.csv)."""
    return category in _EXEMPT


def compute_tax(lines, region, discount_pct=0):
    """Compute sales tax for an order, in integer cents.

    lines:        iterable of dicts {"category": str, "amount_cents": int}
                  (line totals, i.e. quantity * unit price already applied)
    region:       customer region string (key in rates.csv), or None for an
                  unknown customer (0% tax, no discount applied by this module).
    discount_pct: customer discount as a percent number (10 means 10%).

    Returns the tax amount in cents, rounded half up to the cent.
    Raises KeyError for an unknown region string.
    """
    taxable_cents = 0
    for line in lines:
        if is_exempt(line["category"]):
            continue
        amount = line["amount_cents"]
        if not isinstance(amount, int):
            raise TypeError("amount_cents must be an int (cents), got %r" % (amount,))
        taxable_cents += amount

    discount = _to_decimal(discount_pct)
    if not (Decimal(0) <= discount <= Decimal(100)):
        raise ValueError("discount_pct must be between 0 and 100, got %r" % (discount_pct,))

    rate = get_rate(region)

    # Exact decimal arithmetic; only the final tax is rounded.
    base = Decimal(taxable_cents) * (Decimal(100) - discount) / Decimal(100)
    tax = base * rate / Decimal(100)
    return int(tax.quantize(Decimal(1), rounding=ROUND_HALF_UP))
