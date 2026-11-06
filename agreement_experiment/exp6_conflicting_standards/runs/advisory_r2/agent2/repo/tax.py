"""Tax module. Owned by agent2. Computes sales tax.

The data files and rules are in data_tax/ next to this file (see data_tax/RULES.md).

Committed team API (decision log: tax.api v2, tax.unknown_customer v2):

    compute_tax(region, lines, discount) -> float
        region   : region string exactly as in data_tax/rates.csv (e.g. "TX"),
                   or None for an unknown customer (tax is 0.0).
        lines    : list of [category, amount] with GROSS amounts in float dollars
                   (before discount). Categories listed in exempt_categories.csv
                   are not taxed.
        discount : customer discount as a fraction (0.10 = 10%); 0.0 if none.
        returns  : tax in float dollars, rounded to the cent (half up).

    tax_rate(region) -> float | None
        Tax rate as a fraction (0.0825 for TX). Returns None if the region is not
        in rates.csv (lookup_miss = None). tax_rate(None) -> 0.0.

Internal arithmetic uses Decimal so that rounding is exact. Floats are converted
with their shortest decimal representation (str(x)) before any arithmetic.
"""

import csv
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

_DATA_DIR = Path(__file__).resolve().parent / "data_tax"
_CENT = Decimal("0.01")
_HUNDRED = Decimal("100")


def _load_rates(path):
    """Return {region: tax_pct as Decimal (percent number, e.g. 8.25)}."""
    rates = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            region = row["region"].strip()
            if region:
                rates[region] = Decimal(row["tax_pct"].strip())
    return rates


def _load_exempt_categories(path):
    """Return the set of category names that are not taxed."""
    exempt = set()
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            category = row["category"].strip()
            if category:
                exempt.add(category)
    return exempt


_RATES_PCT = _load_rates(_DATA_DIR / "rates.csv")
_EXEMPT = _load_exempt_categories(_DATA_DIR / "exempt_categories.csv")


def _to_decimal(value):
    """Convert an int/float/str amount to Decimal without binary float artifacts."""
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def tax_rate(region):
    """Return the tax rate as a fraction for a region, None if unknown, 0.0 for None."""
    if region is None:
        return 0.0
    pct = _RATES_PCT.get(region)
    if pct is None:
        return None
    return float(pct / _HUNDRED)


def compute_tax(region, lines, discount):
    """Return the sales tax in float dollars, rounded to the cent (half up).

    Follows data_tax/RULES.md:
      taxable_amount = sum of gross amounts of lines whose category is not exempt
      base           = taxable_amount * (100 - discount_pct) / 100
      tax            = base * tax_pct / 100, rounded to the cent (half up)
    """
    if region is None:
        # Unknown customer pays 0% tax (RULES.md).
        return 0.0

    if region not in _RATES_PCT:
        raise ValueError(
            f"no sales-tax rate for region {region!r} (not in data_tax/rates.csv)"
        )

    discount_frac = _to_decimal(discount)
    if not (Decimal("0") <= discount_frac <= Decimal("1")):
        raise ValueError(f"discount must be a fraction between 0 and 1, got {discount!r}")

    taxable_amount = Decimal("0")
    for category, amount in lines:
        if category in _EXEMPT:
            continue
        taxable_amount += _to_decimal(amount)

    base = taxable_amount * (Decimal("1") - discount_frac)
    tax = base * _RATES_PCT[region] / _HUNDRED
    return float(tax.quantize(_CENT, rounding=ROUND_HALF_UP))
