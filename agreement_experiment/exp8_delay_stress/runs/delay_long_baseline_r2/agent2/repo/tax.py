"""Tax module. Owned by agent2. Computes sales tax.

The data files and rules are in data_tax/ next to this file.

Conventions (team standard):
- Money amounts are integers in cents (1250 means $12.50).
- Percentages are percent numbers (10% is 10, 8.25% is 8.25).
- A lookup that finds nothing raises KeyError.

Rules (see data_tax/RULES.md):
- Tax percent depends on the customer's region (rates.csv).
- Items whose category is listed in exempt_categories.csv are not taxed.
- base = taxable_amount * (100 - discount_pct) / 100
- tax = base * tax_pct / 100, rounded to the cent (half up).
- An unknown customer (region None) pays 0% tax.
"""

import csv
import os
from decimal import Decimal, ROUND_HALF_UP

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_tax")


def _load_rates(path):
    rates = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            region = row["region"].strip()
            # Decimal keeps percentages such as 8.875 exact.
            rates[region] = Decimal(row["tax_pct"].strip())
    return rates


def _load_exempt(path):
    exempt = set()
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            category = row["category"].strip()
            if category:
                exempt.add(category)
    return frozenset(exempt)


_RATES = _load_rates(os.path.join(_DATA_DIR, "rates.csv"))
_EXEMPT = _load_exempt(os.path.join(_DATA_DIR, "exempt_categories.csv"))


def tax_rate(region):
    """Return the sales tax percent for a region (e.g. 8.25 for "TX").

    Raises KeyError if the region is not in rates.csv.
    """
    if region not in _RATES:
        raise KeyError(f"unknown tax region: {region!r}")
    return float(_RATES[region])


def is_exempt(category):
    """Return True if items in this category are not taxed."""
    return category in _EXEMPT


def compute_tax(lines, region, discount_pct=0):
    """Return the total sales tax in integer cents.

    lines: iterable of dicts {"category": str, "amount_cents": int}.
        amount_cents is the line amount before the customer discount.
        Lines in exempt categories are not taxed.
    region: the customer's region code (e.g. "TX"), or None if the
        customer is unknown (then the tax is 0).
    discount_pct: the customer's discount percent (e.g. 10 for 10%).
        Must be between 0 and 100 inclusive.

    Raises KeyError for an unknown region (when region is not None).
    Raises ValueError for an invalid discount_pct.
    """
    discount = Decimal(str(discount_pct))
    if not (Decimal(0) <= discount <= Decimal(100)):
        raise ValueError(f"discount_pct must be in [0, 100], got {discount_pct!r}")

    if region is None:
        return 0

    rate = _RATES.get(region)
    if rate is None:
        raise KeyError(f"unknown tax region: {region!r}")

    taxable = 0
    for line in lines:
        if is_exempt(line["category"]):
            continue
        amount = line["amount_cents"]
        if not isinstance(amount, int):
            raise TypeError(f"amount_cents must be an int, got {amount!r}")
        taxable += amount

    # All arithmetic in Decimal to avoid float rounding errors.
    base = Decimal(taxable) * (Decimal(100) - discount) / Decimal(100)
    tax = base * rate / Decimal(100)
    return int(tax.quantize(Decimal("1"), rounding=ROUND_HALF_UP))
