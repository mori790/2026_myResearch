"""Tax module. Owned by agent2. Computes sales tax. The data files and rules are in data_tax/ next to this file.

Shared interface (committed as decision tax_api v2):

    compute_tax(region, discount_rate, lines) -> {"tax_rate": float,
                                                  "taxable_base": float,
                                                  "tax": float}

    region        -- US state code such as "TX", or None for an unknown customer (0% tax).
                     An unknown non-empty region code raises KeyError.
    discount_rate -- fraction, e.g. 0.10 means 10% off.
    lines         -- list of {"category": str, "amount": float dollars before discount}.

Money at the boundary is float dollars and rates are fractions. Internally all money
is kept as Decimal cents so that rounding is exact.
"""

import csv
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

_DATA_DIR = Path(__file__).resolve().parent / "data_tax"

_HUNDRED = Decimal(100)


def _load_rates(path):
    """Return {region_code: tax_pct} where tax_pct is a percent number (8.25 means 8.25%)."""
    rates = {}
    with open(path, newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            rates[row["region"].strip()] = Decimal(row["tax_pct"].strip())
    return rates


def _load_exempt_categories(path):
    """Return the set of category names that are not taxed."""
    exempt = set()
    with open(path, newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            name = row["category"].strip()
            if name:
                exempt.add(name)
    return exempt


_TAX_PCT_BY_REGION = _load_rates(_DATA_DIR / "rates.csv")
_EXEMPT_CATEGORIES = _load_exempt_categories(_DATA_DIR / "exempt_categories.csv")


def compute_tax(region, discount_rate, lines):
    """Compute sales tax for one invoice.

    Rules (data_tax/RULES.md):
      * Only lines whose category is not exempt are taxable.
      * base = taxable_amount * (100 - discount_pct) / 100, where the discount is applied
        to the summed taxable amount.
      * tax = base * tax_pct / 100, rounded half-up to the cent (rounded once, at the end).
      * An unknown customer (region None) pays 0%.
    """
    if region is None:
        tax_pct = Decimal(0)
    else:
        tax_pct = _TAX_PCT_BY_REGION[region]  # KeyError for an unknown region code

    discount = Decimal(str(discount_rate))
    if not (Decimal(0) <= discount <= Decimal(1)):
        raise ValueError(f"discount_rate must be a fraction between 0 and 1, got {discount_rate!r}")

    # Sum the taxable line amounts in cents (exact, no float error).
    taxable_cents = Decimal(0)
    for line in lines:
        if line["category"].strip() in _EXEMPT_CATEGORIES:
            continue
        taxable_cents += Decimal(str(line["amount"])) * _HUNDRED

    # Apply the customer's discount to the taxable total.
    base_cents = taxable_cents * (Decimal(1) - discount)

    # Tax in cents, rounded half-up to a whole cent.
    tax_cents = (base_cents * tax_pct / _HUNDRED).quantize(Decimal(1), rounding=ROUND_HALF_UP)

    return {
        "tax_rate": float(tax_pct / _HUNDRED),
        "taxable_base": float(base_cents / _HUNDRED),
        "tax": float(tax_cents / _HUNDRED),
    }
