"""Tax module. Owned by agent2. Computes sales tax. The data files and rules are in data_tax/ next to this file.

Conventions (team standard):
- Money amounts are integers in cents (1250 means $12.50).
- Percentages are percent numbers (10 means 10%, 8.25 means 8.25%).
- A lookup that finds nothing raises KeyError.

Rules (see data_tax/RULES.md):
- Tax percent depends on the customer's region (data_tax/rates.csv).
- Items whose category is listed in data_tax/exempt_categories.csv are not taxed.
- base = taxable_amount * (100 - discount_pct) / 100
- tax  = base * tax_pct / 100, rounded to the cent (half up).
- An unknown customer (region None) pays 0% tax.

Public API:
- compute_tax(lines, region, discount_pct=0) -> int         tax in cents
- tax_details(lines, region, discount_pct=0) -> dict         breakdown for display
- tax_pct_for_region(region) -> Decimal                      KeyError if region unknown
- is_exempt(category) -> bool

`lines` is an iterable of dicts: {"category": str, "amount_cents": int}.
"""

import csv
import os
from decimal import Decimal, ROUND_HALF_UP

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_tax")
_RATES_PATH = os.path.join(_DATA_DIR, "rates.csv")
_EXEMPT_PATH = os.path.join(_DATA_DIR, "exempt_categories.csv")


def _load_rates(path=_RATES_PATH):
    rates = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            region = row["region"].strip().upper()
            rates[region] = Decimal(row["tax_pct"].strip())
    return rates


def _load_exempt(path=_EXEMPT_PATH):
    with open(path, newline="", encoding="utf-8") as f:
        return {row["category"].strip().lower() for row in csv.DictReader(f)
                if row.get("category") and row["category"].strip()}


_RATES = _load_rates()
_EXEMPT = _load_exempt()


def is_exempt(category):
    """True if items in this category are not taxed."""
    return str(category).strip().lower() in _EXEMPT


def tax_pct_for_region(region):
    """Tax percent for a region code (e.g. "TX" -> Decimal("8.25")).

    Raises KeyError if the region is not in rates.csv.
    """
    key = str(region).strip().upper()
    if key not in _RATES:
        raise KeyError(f"no tax rate for region {region!r}")
    return _RATES[key]


def _check_discount(discount_pct):
    d = Decimal(str(discount_pct))
    if d < 0 or d > 100:
        raise ValueError(f"discount_pct must be between 0 and 100, got {discount_pct!r}")
    return d


def tax_details(lines, region, discount_pct=0):
    """Return a breakdown of the sales tax for one order.

    Keys of the returned dict:
      taxable_cents  -- sum of amounts of non-exempt lines (before discount), in cents
      exempt_cents   -- sum of amounts of exempt lines, in cents
      discount_pct   -- discount percent used (number)
      tax_pct        -- tax percent used (Decimal; 0 for an unknown customer)
      tax_cents      -- tax in cents, rounded half up to the cent
    """
    taxable = 0
    exempt = 0
    for line in lines:
        amount = int(line["amount_cents"])
        if is_exempt(line["category"]):
            exempt += amount
        else:
            taxable += amount

    discount = _check_discount(discount_pct)

    if region is None:
        # Unknown customer pays 0% tax.
        tax_pct = Decimal(0)
    else:
        tax_pct = tax_pct_for_region(region)  # KeyError if unknown region

    base = Decimal(taxable) * (Decimal(100) - discount) / Decimal(100)
    tax = (base * tax_pct / Decimal(100)).quantize(Decimal("1"), rounding=ROUND_HALF_UP)

    return {
        "taxable_cents": taxable,
        "exempt_cents": exempt,
        "discount_pct": discount_pct,
        "tax_pct": tax_pct,
        "tax_cents": int(tax),
    }


def compute_tax(lines, region, discount_pct=0):
    """Sales tax in integer cents for one order."""
    return tax_details(lines, region, discount_pct)["tax_cents"]
