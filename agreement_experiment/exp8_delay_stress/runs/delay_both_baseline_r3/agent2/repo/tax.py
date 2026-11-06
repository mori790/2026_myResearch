"""Tax module. Owned by agent2. Computes sales tax.

The data files and rules are in data_tax/ next to this file:
  - data_tax/rates.csv              region -> tax_pct (percent number, e.g. 8.25)
  - data_tax/exempt_categories.csv  item categories that are not taxed
  - data_tax/RULES.md               the rules implemented here

Conventions (team standard):
  - Money amounts are integer cents (1250 == $12.50).
  - Percentages are percent numbers (10 == 10%, 8.25 == 8.25%).
  - A lookup that finds nothing raises KeyError.

Public API (agreed as tax_api, plus tax_percent requested by invoice):
  compute_tax(region, discount_pct, lines) -> int   tax in integer cents
  tax_percent(region) -> Decimal                    tax percent number (8.25 for TX)
"""

import csv
import os
from decimal import Decimal, ROUND_HALF_UP

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_tax")
_HUNDRED = Decimal(100)


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
_EXEMPT = _load_exempt(os.path.join(_DATA_DIR, "exempt_categories.csv"))


def tax_percent(region):
    """Return the tax percent (Decimal, percent number) for a region.

    region None (unknown customer) -> Decimal(0).
    A non-None region not listed in rates.csv raises KeyError.
    """
    if region is None:
        return Decimal(0)
    return _RATES[region]


def compute_tax(region, discount_pct, lines):
    """Compute the sales tax for one order, in integer cents.

    region       : customer region code (e.g. "TX"), or None for an unknown
                   customer, who pays 0% tax. A non-None region missing from
                   rates.csv raises KeyError.
    discount_pct : customer discount as a percent number (10 == 10%); 0 if none.
    lines        : iterable of dicts {"category": str, "amount_cents": int},
                   pre-discount line amounts in integer cents. Lines whose
                   category is listed in exempt_categories.csv are not taxed.

    Rules (data_tax/RULES.md):
      taxable = sum of taxable line amounts
      base    = taxable * (100 - discount_pct) / 100
      tax     = base * tax_pct / 100, rounded to the cent (half up)

    All arithmetic is exact (Decimal); rounding happens once, at the end.
    """
    discount = Decimal(str(discount_pct))
    if not (Decimal(0) <= discount <= _HUNDRED):
        raise ValueError(f"discount_pct must be between 0 and 100, got {discount_pct!r}")

    lines = list(lines)
    for line in lines:
        amount = line["amount_cents"]
        if not isinstance(amount, int) or isinstance(amount, bool):
            raise TypeError(f"amount_cents must be int, got {amount!r}")

    if region is None:
        return 0

    pct = tax_percent(region)  # KeyError for unknown region

    taxable = sum(
        Decimal(line["amount_cents"])
        for line in lines
        if line["category"] not in _EXEMPT
    )
    base = taxable * (_HUNDRED - discount) / _HUNDRED
    tax = base * pct / _HUNDRED
    return int(tax.quantize(Decimal(1), rounding=ROUND_HALF_UP))
