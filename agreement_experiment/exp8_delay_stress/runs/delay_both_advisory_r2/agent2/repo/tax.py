"""Tax module. Owned by agent2. Computes sales tax.

Implements the committed decisions TAX_API (v2) and TAX_UNKNOWN_REGION (v1):

- Money is integer cents (1250 == $12.50).
- Percentages are percent numbers (10 == 10%, 8.25 == 8.25%).
- compute_tax(region, lines, discount_pct) -> int   (tax in integer cents)
- tax_rate_pct(region) -> float                     (tax percent, e.g. 8.25)
- An unknown non-empty region code raises KeyError.
- region None or "" (unknown customer) means 0% tax.

The data files and rules live in data_tax/ next to this file (see data_tax/RULES.md).
"""

import csv
import os
from decimal import ROUND_HALF_UP, Decimal

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_tax")


def _load_rates(path):
    rates = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            region = row["region"].strip()
            rates[region] = Decimal(row["tax_pct"].strip())
    return rates


def _load_exempt(path):
    exempt = set()
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            category = row["category"].strip()
            if category:
                exempt.add(category)
    return exempt


_RATES = _load_rates(os.path.join(_DATA_DIR, "rates.csv"))
_EXEMPT_CATEGORIES = _load_exempt(os.path.join(_DATA_DIR, "exempt_categories.csv"))


def _is_unknown_customer(region):
    return region is None or (isinstance(region, str) and region.strip() == "")


def _rate_for(region):
    """Return the tax percent as a Decimal. Unknown customer -> 0. Unknown region -> KeyError."""
    if _is_unknown_customer(region):
        return Decimal(0)
    return _RATES[region.strip()]  # raises KeyError if the region is not in rates.csv


def tax_rate_pct(region):
    """Return the sales tax percent for a region (e.g. 8.25 for TX).

    Returns 0 for region None or "" (unknown customer).
    Raises KeyError for an unknown region code.
    """
    return float(_rate_for(region))


def compute_tax(region, lines, discount_pct):
    """Return the total sales tax for an invoice, in integer cents.

    region       -- customer region code (e.g. "TX"), or None for an unknown customer.
    lines        -- list of {"category": str, "amount_cents": int}, one per invoice line.
    discount_pct -- customer discount as a percent number (10 means 10%); 0 if none.

    Rules (data_tax/RULES.md):
      taxable = sum of amount_cents over lines whose category is not exempt
      base    = taxable * (100 - discount_pct) / 100
      tax     = base * tax_pct / 100, rounded half up to the cent (once, on the total)
    """
    rate = _rate_for(region)

    if isinstance(discount_pct, bool) or not isinstance(discount_pct, (int, float, Decimal)):
        raise TypeError("discount_pct must be a number (percent), got %r" % (discount_pct,))
    discount = Decimal(str(discount_pct))
    if discount < 0 or discount > 100:
        raise ValueError("discount_pct must be between 0 and 100, got %r" % (discount_pct,))

    taxable = 0
    for line in lines:
        amount = line["amount_cents"]
        if isinstance(amount, bool) or not isinstance(amount, int):
            raise TypeError("amount_cents must be an int (cents), got %r" % (amount,))
        if line["category"].strip() not in _EXEMPT_CATEGORIES:
            taxable += amount

    if taxable == 0 or rate == 0:
        return 0

    # tax = taxable * (100 - d) / 100 * rate / 100 cents, computed exactly with Decimal,
    # then rounded half up to a whole cent (the total is rounded once).
    exact_tax_cents = (Decimal(taxable) * (Decimal(100) - discount) * rate) / Decimal(10000)
    return int(exact_tax_cents.quantize(Decimal(1), rounding=ROUND_HALF_UP))
