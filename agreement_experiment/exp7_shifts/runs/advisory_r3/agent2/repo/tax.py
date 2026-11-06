"""Tax module. Owned by agent2. Computes sales tax.

The data files and rules are in data_tax/ next to this file (see data_tax/RULES.md).

Interface (committed decision: tax_api v1):
  compute_tax(customer, lines) -> float   tax in dollars, rounded half-up to the cent
  tax_rate(region) -> float               rate as a fraction (8.25% -> 0.0825)

Units follow pricing_api: money is a float in dollars, percentages are fractions.
Internally, arithmetic uses Decimal so that cent rounding is exact.
"""

import csv
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

_DATA_DIR = Path(__file__).resolve().parent / "data_tax"
_CENT = Decimal("0.01")
_HUNDRED = Decimal("100")


def _load_rates():
    """region -> rate as Decimal fraction (rates.csv stores percent numbers)."""
    rates = {}
    with open(_DATA_DIR / "rates.csv", newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            region = row["region"].strip()
            percent = Decimal(row["tax_pct"].strip())
            rates[region] = percent / _HUNDRED
    return rates


def _load_exempt_categories():
    """Set of category names (normalized) that are not taxed."""
    with open(_DATA_DIR / "exempt_categories.csv", newline="", encoding="utf-8") as f:
        return {
            row["category"].strip().lower()
            for row in csv.DictReader(f)
            if row.get("category") and row["category"].strip()
        }


_RATES = _load_rates()
_EXEMPT = _load_exempt_categories()


def tax_rate(region):
    """Return the sales tax rate for region as a fraction (e.g. 'TX' -> 0.0825).

    Raises KeyError if the region is not in rates.csv.
    """
    if region not in _RATES:
        raise KeyError(f"no tax rate for region {region!r}")
    return float(_RATES[region])


def _is_exempt(category):
    return str(category).strip().lower() in _EXEMPT


def compute_tax(customer, lines):
    """Return the sales tax in dollars for one order.

    customer: dict from pricing.get_customer ('region', 'discount' as fraction),
              or None for an unknown customer, who pays 0 tax.
    lines:    list of {'category': str, 'amount': float}, where amount is the
              line total in dollars before discount.

    Rules (RULES.md):
      taxable = sum of amounts of lines whose category is not exempt
      base    = taxable * (1 - discount)
      tax     = base * rate, rounded half-up to the cent
    """
    if customer is None:
        return 0.0

    taxable = Decimal("0")
    for line in lines:
        if not _is_exempt(line["category"]):
            taxable += Decimal(str(line["amount"]))

    discount = Decimal(str(customer.get("discount", 0.0)))
    region = customer["region"]
    if region not in _RATES:
        raise KeyError(f"no tax rate for region {region!r}")
    rate = _RATES[region]

    base = taxable * (Decimal("1") - discount)
    tax = (base * rate).quantize(_CENT, rounding=ROUND_HALF_UP)
    return float(tax)
