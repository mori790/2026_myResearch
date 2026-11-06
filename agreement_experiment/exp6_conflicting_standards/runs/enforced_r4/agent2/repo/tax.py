"""Tax module. Owned by agent2. Computes sales tax. The data files and rules are in data_tax/ next to this file.

Agreed API (decision topic 'tax_api'):

    compute_tax(lines, region, discount_pct) -> dict

    lines        list of {"category": str, "amount_cents": int}
                 line amounts before discount, integer cents
    region       str region code (e.g. "TX") or None
                 None = unknown customer -> tax 0, tax_pct 0
    discount_pct number, percent (10 means 10%), 0 if no discount

    returns      {"taxable_cents": int, "tax_cents": int, "tax_pct": number}

Rules (data_tax/RULES.md):
    taxable   = sum of line amounts whose category is NOT in exempt_categories.csv
    base      = taxable * (100 - discount_pct) / 100
    tax       = base * tax_pct / 100, rounded to the cent (half up)
    unknown customer (region None) pays 0%
"""

import csv
import os
from decimal import Decimal, ROUND_HALF_UP

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_tax")


def _load_rates(path):
    rates = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            region = row["region"].strip().upper()
            # Keep percent as Decimal from the string to avoid float error.
            rates[region] = Decimal(row["tax_pct"].strip())
    return rates


def _load_exempt(path):
    exempt = set()
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            category = row["category"].strip().lower()
            if category:
                exempt.add(category)
    return frozenset(exempt)


_RATES = _load_rates(os.path.join(_DATA_DIR, "rates.csv"))
_EXEMPT = _load_exempt(os.path.join(_DATA_DIR, "exempt_categories.csv"))


def _rate_for(region):
    """Return the tax percent (Decimal) for a region; None means unknown customer (0%).

    Raises KeyError if region is a non-null string that is not in rates.csv.
    """
    if region is None:
        return Decimal("0")
    return _RATES[region.strip().upper()]


def _is_taxable(category):
    return category.strip().lower() not in _EXEMPT


def compute_tax(lines, region, discount_pct):
    """Compute sales tax for an order. See module docstring for the agreed API."""
    if isinstance(discount_pct, bool) or not 0 <= Decimal(str(discount_pct)) <= 100:
        raise ValueError("discount_pct must be a percent between 0 and 100")

    taxable_cents = 0
    for line in lines:
        amount = line["amount_cents"]
        if isinstance(amount, bool) or not isinstance(amount, int):
            raise TypeError("amount_cents must be an integer number of cents")
        if _is_taxable(line["category"]):
            taxable_cents += amount

    tax_pct = _rate_for(region)

    base = Decimal(taxable_cents) * (Decimal("100") - Decimal(str(discount_pct))) / Decimal("100")
    tax = (base * tax_pct / Decimal("100")).quantize(Decimal("1"), rounding=ROUND_HALF_UP)

    return {
        "taxable_cents": taxable_cents,
        "tax_cents": int(tax),
        "tax_pct": float(tax_pct),
    }
