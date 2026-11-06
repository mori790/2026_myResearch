"""Tax module. Owned by agent2. Computes sales tax.

The data files and rules are in data_tax/ next to this file.

Public API (committed decisions tax_api and tax_unknown_region):

    compute_tax(lines, region, discount_pct=0) -> int
        lines        : list of (category: str, amount_cents: int) for ALL line
                       items of the order (taxable and exempt).
        region       : region code of the customer (e.g. "TX"), or None for an
                       unknown customer (tax is 0).
        discount_pct : customer discount in percent numbers (10 means 10%),
                       0..100, default 0.
        returns      : total tax for the order in integer cents.

    tax_rate(region) -> float   (percent number, e.g. 8.25; None -> 0)
    is_exempt(category) -> bool

Conventions: money is integer cents, percentages are percent numbers.
A lookup that finds nothing raises KeyError (unknown non-None region).
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
    exempt = set()
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            category = (row.get("category") or "").strip()
            if category:
                exempt.add(category)
    return exempt


_RATES = _load_rates(os.path.join(_DATA_DIR, "rates.csv"))
_EXEMPT = _load_exempt(os.path.join(_DATA_DIR, "exempt_categories.csv"))


def tax_rate(region):
    """Return the sales tax rate for a region as a percent number.

    None (unknown customer) gives 0. A non-None region not in rates.csv
    raises KeyError.
    """
    if region is None:
        return 0.0
    return float(_RATES[region])


def is_exempt(category):
    """True if items of this category are not taxed (exact, case-sensitive match)."""
    return category in _EXEMPT


def compute_tax(lines, region, discount_pct=0):
    """Compute the total sales tax for an order, in integer cents.

    Rule (data_tax/RULES.md):
        taxable    = sum of amounts of non-exempt lines
        base       = taxable * (100 - discount_pct) / 100
        tax        = base * tax_pct / 100, rounded to the cent (half up)

    Arithmetic uses Decimal so no floating-point error is introduced; rounding
    happens once, at the end.
    """
    discount = _check_discount(discount_pct)

    taxable_cents = 0
    for category, amount_cents in lines:
        if isinstance(amount_cents, bool) or not isinstance(amount_cents, int):
            raise TypeError(
                f"amount_cents must be an int (cents), got {amount_cents!r}"
            )
        if not is_exempt(category):
            taxable_cents += amount_cents

    if region is None:
        return 0

    rate = _RATES[region]  # KeyError for an unknown region
    base = Decimal(taxable_cents) * (Decimal(100) - discount) / Decimal(100)
    tax = base * rate / Decimal(100)
    return int(tax.quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def _check_discount(discount_pct):
    if isinstance(discount_pct, bool):
        raise TypeError("discount_pct must be a number, got bool")
    try:
        discount = Decimal(str(discount_pct))
    except Exception as exc:  # e.g. non-numeric string
        raise TypeError(f"discount_pct must be a number, got {discount_pct!r}") from exc
    if not discount.is_finite() or discount < 0 or discount > 100:
        raise ValueError(f"discount_pct must be between 0 and 100, got {discount_pct!r}")
    return discount
