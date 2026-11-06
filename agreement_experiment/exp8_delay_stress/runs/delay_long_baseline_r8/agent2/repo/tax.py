"""Tax module. Owned by agent2. Computes sales tax.

The data files and rules are in data_tax/ next to this file.

Conventions (team standard):
- Money amounts are integers in cents (1250 means $12.50).
- Percentages are percent numbers (10% is 10, 8.25% is 8.25).
- A lookup that finds nothing raises KeyError.

Public API:
- tax_pct(region)                      -> Fraction, percent for a region.
                                          region=None means unknown customer -> 0.
- is_exempt(category)                  -> bool.
- taxable_amount_cents(lines)          -> int, sum of non-exempt line amounts.
- compute_tax_cents(taxable_cents, region, discount_pct) -> int
- compute_invoice_tax(lines, region, discount_pct)       -> int
    lines: iterable of (category, amount_cents) pairs.

Rounding: only the final tax is rounded, to the cent, half up
(half away from zero for negative amounts). Intermediate values are exact
(fractions), so no float error is introduced.
"""

import csv
from fractions import Fraction
from pathlib import Path

_DATA_DIR = Path(__file__).resolve().parent / "data_tax"


def _load_rates():
    rates = {}
    with open(_DATA_DIR / "rates.csv", newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            region = row["region"].strip().upper()
            rates[region] = Fraction(row["tax_pct"].strip())
    return rates


def _load_exempt():
    exempt = set()
    with open(_DATA_DIR / "exempt_categories.csv", newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            cat = row["category"].strip().lower()
            if cat:
                exempt.add(cat)
    return frozenset(exempt)


_RATES = _load_rates()
_EXEMPT = _load_exempt()


def tax_pct(region):
    """Return the sales tax percent (e.g. 8.25) for a customer's region.

    region=None (or empty) means the customer is unknown; such customers pay 0%.
    A region that is not in rates.csv raises KeyError.
    """
    if region is None or str(region).strip() == "":
        return Fraction(0)
    key = str(region).strip().upper()
    if key not in _RATES:
        raise KeyError(f"no tax rate for region {region!r}")
    return _RATES[key]


def is_exempt(category):
    """True if items in this category are not taxed (see exempt_categories.csv)."""
    return str(category).strip().lower() in _EXEMPT


def taxable_amount_cents(lines):
    """Sum of line amounts (cents) whose category is not exempt.

    lines: iterable of (category, amount_cents) pairs.
    """
    return sum(amount for category, amount in lines if not is_exempt(category))


def _round_half_up(x):
    """Round an exact Fraction to an int; ties go away from zero."""
    if x >= 0:
        return int(x + Fraction(1, 2))  # floor for x >= 0
    return -int(-x + Fraction(1, 2))


def compute_tax_cents(taxable_cents, region, discount_pct=0):
    """Sales tax in cents for a taxable amount.

    base = taxable_cents * (100 - discount_pct) / 100
    tax  = base * tax_pct(region) / 100, rounded to the cent (half up).

    discount_pct: customer's discount percent (e.g. 10 for 10%). Default 0.
    """
    if isinstance(taxable_cents, bool) or not isinstance(taxable_cents, int):
        raise TypeError("taxable_cents must be an int (cents)")
    discount = Fraction(discount_pct)
    if not 0 <= discount <= 100:
        raise ValueError(f"discount_pct must be in [0, 100], got {discount_pct!r}")
    rate = tax_pct(region)
    base = Fraction(taxable_cents) * (100 - discount) / 100
    tax = base * rate / 100
    return _round_half_up(tax)


def compute_invoice_tax(lines, region, discount_pct=0):
    """Sales tax in cents for a whole order.

    lines: iterable of (category, amount_cents) pairs. Exempt lines are skipped.
    The tax is computed once on the summed taxable amount, not per line.
    """
    lines = list(lines)
    return compute_tax_cents(taxable_amount_cents(lines), region, discount_pct)
