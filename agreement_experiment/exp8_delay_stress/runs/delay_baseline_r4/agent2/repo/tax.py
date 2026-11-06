"""Tax module. Owned by agent2. Computes sales tax.

The data files and rules are in data_tax/ next to this file (see data_tax/RULES.md).

Conventions (team standard):
- Money amounts are integers in cents (1250 means $12.50).
- Percentages are percent numbers (10 means 10%, 8.25 means 8.25%).
- A lookup that finds nothing raises KeyError, except an unknown customer
  (region is None), which pays 0% tax.

Public API:
- get_tax_pct(region)            -> float   tax percent for a region
- is_exempt(category)            -> bool    True if the category is tax-exempt
- compute_tax(lines, region, discount_pct) -> int   tax in integer cents
"""

import csv
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

_DATA_DIR = Path(__file__).resolve().parent / "data_tax"
_RATES_FILE = _DATA_DIR / "rates.csv"
_EXEMPT_FILE = _DATA_DIR / "exempt_categories.csv"


def _load_rates(path=_RATES_FILE):
    """Return {region: tax_pct} as Decimal values, read from rates.csv."""
    rates = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            rates[row["region"].strip()] = Decimal(row["tax_pct"].strip())
    return rates


def _load_exempt_categories(path=_EXEMPT_FILE):
    """Return the set of tax-exempt category names, read from exempt_categories.csv."""
    with open(path, newline="", encoding="utf-8") as f:
        return {row["category"].strip() for row in csv.DictReader(f) if row["category"].strip()}


_RATES = _load_rates()
_EXEMPT = _load_exempt_categories()


def get_tax_pct(region):
    """Return the tax percent for `region` (e.g. 8.25 for "TX").

    region=None means the customer is unknown; such a customer pays 0%.
    A non-empty region that is not in rates.csv raises KeyError.
    """
    if region is None:
        return 0.0
    if region not in _RATES:
        raise KeyError(f"no tax rate for region {region!r}")
    return float(_RATES[region])


def is_exempt(category):
    """Return True if items of `category` are not taxed (listed in exempt_categories.csv)."""
    return category in _EXEMPT


def compute_tax(lines, region, discount_pct):
    """Return the sales tax for an order, in integer cents.

    lines        -- list of {"category": str, "amount_cents": int}; amount_cents is
                    the line amount (price * quantity) in cents, before discount.
    region       -- customer's region (e.g. "TX"), or None for an unknown customer.
    discount_pct -- customer's discount as a percent number (10 means 10%).

    Rules (data_tax/RULES.md):
      taxable_sum = sum of amount_cents over non-exempt lines
      base        = taxable_sum * (100 - discount_pct) / 100
      tax         = base * tax_pct / 100, rounded half up to the cent
    """
    taxable_sum = 0
    for line in lines:
        if not is_exempt(line["category"]):
            taxable_sum += int(line["amount_cents"])

    pct = Decimal(str(get_tax_pct(region)))
    discount = Decimal(str(discount_pct))

    # base * tax_pct / 100 with base = taxable_sum * (100 - discount) / 100
    # => tax = taxable_sum * (100 - discount) * tax_pct / 10000
    # Decimal keeps this exact, so the only rounding is the final half-up step.
    tax = Decimal(taxable_sum) * (Decimal(100) - discount) * pct / Decimal(10000)
    return int(tax.quantize(Decimal("1"), rounding=ROUND_HALF_UP))
