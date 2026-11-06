"""Tax module. Owned by agent2. Computes sales tax.

The data files and rules are in data_tax/ next to this file.

Committed interface (TAX_API v2, TAX_UNKNOWN_REGION v1):

    compute_tax(lines, region, discount_rate) -> (tax_dollars, tax_rate)

    lines         list of (category: str, line_amount_dollars: float)
                  line_amount = quantity * unit_price, computed by the caller.
    region        customer region code (e.g. "TX"), or None for an unknown customer.
    discount_rate customer discount as a fraction (0.10 = 10% off); 0.0 if none.
    tax_dollars   float dollars, rounded to the cent (half up).
    tax_rate      region rate as a fraction (0.0825 for TX).

Unknown customer (region None) -> (0.0, 0.0).
A non-None region missing from rates.csv raises KeyError.

Internally all arithmetic uses Decimal, and the only rounding is the final
rounding of the tax amount to the cent (half up).
"""

import csv
import os
from decimal import Decimal, ROUND_HALF_UP

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_tax")
_CENT = Decimal("0.01")
_HUNDRED = Decimal("100")


def _load_rates(path):
    """Return {region: Decimal percent}, e.g. {"TX": Decimal("8.25")}."""
    rates = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            region = row["region"].strip()
            rates[region] = Decimal(row["tax_pct"].strip())
    return rates


def _load_exempt(path):
    """Return the set of exempt category names."""
    exempt = set()
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            category = row["category"].strip()
            if category:
                exempt.add(category)
    return exempt


_RATES = _load_rates(os.path.join(_DATA_DIR, "rates.csv"))
_EXEMPT_CATEGORIES = _load_exempt(os.path.join(_DATA_DIR, "exempt_categories.csv"))


def compute_tax(lines, region, discount_rate):
    """Compute sales tax for one order.

    Returns (tax_dollars, tax_rate). See the module docstring for the contract.
    """
    if region is None:
        # Unknown customer pays 0% tax (RULES.md).
        return (0.0, 0.0)

    rate_pct = _RATES[region]  # KeyError for an unknown region code

    taxable = Decimal("0")
    for category, line_amount in lines:
        if category.strip() in _EXEMPT_CATEGORIES:
            continue
        taxable += Decimal(str(line_amount))

    # base = taxable_amount * (100 - discount_pct) / 100
    discount = Decimal(str(discount_rate))
    base = taxable * (Decimal("1") - discount)

    # tax = base * tax_pct / 100, rounded to the cent (half up)
    tax = (base * rate_pct / _HUNDRED).quantize(_CENT, rounding=ROUND_HALF_UP)

    tax_rate = rate_pct / _HUNDRED
    return (float(tax), float(tax_rate))
