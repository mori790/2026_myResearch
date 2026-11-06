"""Tax module. Owned by agent2. Computes sales tax.

The data files and rules are in data_tax/ next to this file (see data_tax/RULES.md).

Public API (agreed in the shared decision log as TAX_API v2):

    compute_tax(region, discount_pct, lines) -> int
        Tax amount in integer cents (>= 0).
        region       : rates.csv region code (e.g. "TX"), or None when the customer has no region (0% tax).
                       An unrecognized non-None region raises KeyError.
        discount_pct : percent number (10 means 10% off); 0 if there is no discount.
        lines        : list of {"category": str, "amount_cents": int}; amount_cents is the line
                       total in integer cents before discount. Lines whose category is listed in
                       exempt_categories.csv are not taxed.

    tax_percent(region) -> Decimal
        Tax percent for the region (e.g. Decimal("8.25") for TX). 0 when region is None.
        An unrecognized non-None region raises KeyError.

Conventions: money is integer cents, percentages are percent numbers. Callers must convert
dollars and fractions before calling this module; non-integer amounts raise TypeError.
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
            rates[region] = Decimal(row["tax_pct"].strip())
    return rates


def _load_exempt(path):
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return {row["category"].strip() for row in reader if row.get("category", "").strip()}


_RATES = _load_rates(os.path.join(_DATA_DIR, "rates.csv"))
_EXEMPT_CATEGORIES = _load_exempt(os.path.join(_DATA_DIR, "exempt_categories.csv"))


def _rate_for(region):
    """Return the tax percent for region. None means no region, so 0%. Unknown region raises KeyError."""
    if region is None:
        return Decimal("0")
    return _RATES[region]  # KeyError if the region is unknown


def tax_percent(region):
    """Tax percent (Decimal, e.g. Decimal("8.25")) for the region. 0 for region None."""
    return _rate_for(region)


def _check_cents(value, name):
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be an integer number of cents, got {value!r}")
    if value < 0:
        raise ValueError(f"{name} must be non-negative, got {value}")


def compute_tax(region, discount_pct, lines):
    """Return the sales tax in integer cents for an invoice.

    Steps (see data_tax/RULES.md):
      1. taxable = sum of amount_cents over lines whose category is not exempt.
      2. base = taxable * (100 - discount_pct) / 100   (exact decimal arithmetic)
      3. tax  = base * tax_pct / 100, rounded half up to the whole cent.
    Tax is computed once on the invoice total, not per line.
    """
    rate = _rate_for(region)

    discount = Decimal(str(discount_pct)) if not isinstance(discount_pct, Decimal) else discount_pct
    if not (Decimal("0") <= discount <= Decimal("100")):
        raise ValueError(f"discount_pct must be between 0 and 100, got {discount_pct!r}")

    taxable = 0
    for line in lines:
        amount = line["amount_cents"]
        _check_cents(amount, "amount_cents")
        if line["category"] not in _EXEMPT_CATEGORIES:
            taxable += amount

    if taxable == 0:
        return 0

    base = Decimal(taxable) * (Decimal("100") - discount) / Decimal("100")
    tax = base * rate / Decimal("100")
    return int(tax.quantize(Decimal("1"), rounding=ROUND_HALF_UP))
