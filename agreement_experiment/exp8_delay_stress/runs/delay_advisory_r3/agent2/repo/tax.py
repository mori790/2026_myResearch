"""Tax module. Owned by agent2. Computes sales tax.

The data files and rules are in data_tax/ next to this file.

Committed team decisions this module follows (see the shared agreement log):
- TAX_API (v3):
    compute_tax(lines, region, discount) -> int
        lines    : list of {"category": str, "amount_cents": int}
                   (amount_cents = line total in integer cents before customer discount)
        region   : customer region string as in pricing (e.g. "TX"); None = unknown customer (tax 0)
        discount : customer discount as a fraction (0.10 = 10%), 0.0 if none
        returns  : total tax in integer cents, computed once on the taxable total,
                   rounded half up to the cent
    tax.rate(region) -> float
        returns  : tax rate as a fraction (0.0825 for TX), 0.0 for region None,
                   KeyError for a region not in rates.csv
- TAX_UNKNOWN_REGION (v1): region None -> 0 tax without error;
  a non-empty region not in rates.csv -> KeyError.
- Team standard: money is integer cents; percentages in the API are fractions
  at the boundary; a failed lookup raises KeyError.

Rules (data_tax/RULES.md):
    taxable    = sum of amount_cents of lines whose category is NOT exempt
    base       = taxable * (1 - discount)
    tax        = base * rate, rounded half up to the cent
"""

import csv
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

_DATA_DIR = Path(__file__).resolve().parent / "data_tax"


def _load_rates(path):
    """Return {region: Decimal percent} loaded from rates.csv (percent numbers, e.g. 8.25)."""
    rates = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            region = row["region"].strip()
            rates[region] = Decimal(row["tax_pct"].strip())
    return rates


def _load_exempt_categories(path):
    """Return the set of category names that are not taxed."""
    with open(path, newline="", encoding="utf-8") as f:
        return {row["category"].strip() for row in csv.DictReader(f) if row["category"].strip()}


_RATES_PCT = _load_rates(_DATA_DIR / "rates.csv")
_EXEMPT_CATEGORIES = _load_exempt_categories(_DATA_DIR / "exempt_categories.csv")


def rate(region):
    """Tax rate for a customer region as a fraction (0.0825 for TX).

    region None (unknown customer) -> 0.0.
    A region not in rates.csv -> KeyError.
    """
    return float(_rate_decimal(region))


def _rate_decimal(region):
    """Exact Decimal fraction used for the calculation (same rules as rate())."""
    if region is None:
        return Decimal(0)
    if region not in _RATES_PCT:
        raise KeyError(f"no tax rate for region {region!r}")
    return _RATES_PCT[region] / Decimal(100)


def compute_tax(lines, region, discount):
    """Total sales tax for an order, in integer cents.

    lines    : iterable of {"category": str, "amount_cents": int}
    region   : customer region (e.g. "TX"), or None for an unknown customer (tax 0)
    discount : customer discount as a fraction (0.10 = 10%), 0.0 if none
    """
    rate_frac = _rate_decimal(region)

    taxable_cents = 0
    for line in lines:
        if line["category"] in _EXEMPT_CATEGORIES:
            continue
        taxable_cents += int(line["amount_cents"])

    # Use Decimal(str(...)) so a float discount such as 0.1 is exact.
    discount_frac = Decimal(str(discount))
    base = Decimal(taxable_cents) * (Decimal(1) - discount_frac)
    tax = base * rate_frac

    # Round once, on the total, half up to the cent.
    return int(tax.quantize(Decimal(1), rounding=ROUND_HALF_UP))
