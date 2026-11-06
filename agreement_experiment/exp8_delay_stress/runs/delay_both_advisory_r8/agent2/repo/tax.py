"""Tax module. Owned by agent2. Computes sales tax.

The data files and rules are in data_tax/ next to this file:
  - rates.csv               region -> tax percent
  - exempt_categories.csv   item categories that are not taxed
  - RULES.md                the tax rules

Agreed interface (shared decision log: TAX_API v2, UNKNOWN_CUSTOMER v1,
money_representation v3, percent_representation v3):

  compute_tax(region, discount_pct, lines) -> int
      region        str or None. Customer region code from pricing (e.g. "TX").
                    None means unknown customer: tax is 0.
                    A non-None region that is not in rates.csv raises KeyError.
      discount_pct  number, PERCENT (10 means 10% off).
      lines         list of (category: str, amount_cents: int) tuples, one per
                    invoice line. amount_cents is the UNDISCOUNTED line amount
                    (quantity * unit price). The discount is applied here, once.
      returns       tax in integer cents.
                    base = (sum of non-exempt amounts) * (100 - discount_pct) / 100
                    tax  = base * rate / 100, rounded half up to the cent, once.

  tax_rate(region) -> number, PERCENT (8.25 for TX).
      0 for None (unknown customer). KeyError for an unknown non-None region.
"""

import csv
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

_DATA_DIR = Path(__file__).resolve().parent / "data_tax"


def _load_rates(path):
    """Return {region: Decimal percent} from rates.csv."""
    rates = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            region = (row.get("region") or "").strip()
            pct = (row.get("tax_pct") or "").strip()
            if not region or not pct:
                continue
            rates[region] = Decimal(pct)
    return rates


def _load_exempt(path):
    """Return the set of exempt categories (normalized) from exempt_categories.csv."""
    exempt = set()
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            category = (row.get("category") or "").strip().lower()
            if category:
                exempt.add(category)
    return exempt


_RATES = _load_rates(_DATA_DIR / "rates.csv")
_EXEMPT = _load_exempt(_DATA_DIR / "exempt_categories.csv")

def _rate_for(region):
    """Exact tax rate as Decimal percent. None -> 0. Unknown region -> KeyError."""
    if region is None:
        return Decimal(0)
    key = region.strip() if isinstance(region, str) else region
    if key not in _RATES:
        raise KeyError(f"unknown tax region: {region!r}")
    return _RATES[key]


def tax_rate(region):
    """Tax rate for a region, as a percent number (8.25 means 8.25%).

    Returns 0 for None (unknown customer). Raises KeyError for an unknown
    non-None region.
    """
    return float(_rate_for(region))


def is_exempt(category):
    """True if items in this category are not taxed."""
    return str(category).strip().lower() in _EXEMPT


def compute_tax(region, discount_pct, lines):
    """Return the sales tax for an invoice, in integer cents.

    See the module docstring for the agreed interface.
    """
    rate = _rate_for(region)

    discount = Decimal(str(discount_pct))
    if discount < 0 or discount > 100:
        raise ValueError(f"discount_pct must be between 0 and 100, got {discount_pct!r}")

    taxable_cents = 0
    for category, amount_cents in lines:
        if isinstance(amount_cents, bool) or not isinstance(amount_cents, int):
            raise TypeError(f"amount_cents must be int, got {amount_cents!r}")
        if amount_cents < 0:
            raise ValueError(f"amount_cents must not be negative, got {amount_cents!r}")
        if not is_exempt(category):
            taxable_cents += amount_cents

    if taxable_cents == 0 or rate == 0:
        return 0

    # Base after the customer's discount, in cents (exact, not rounded yet).
    base = Decimal(taxable_cents) * (Decimal(100) - discount) / Decimal(100)
    # Tax in cents, rounded half up once at the end.
    tax = base * rate / Decimal(100)
    return int(tax.quantize(Decimal("1"), rounding=ROUND_HALF_UP))
