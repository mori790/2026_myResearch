"""Tax module. Owned by agent2. Computes sales tax.

The data files and rules are in data_tax/ next to this file.

API (committed decision: tax_api v1)
------------------------------------
calculate_tax(lines, region, discount=0.0) -> float

- lines:    list of {"category": str, "amount": float}
            amount = UNDISCOUNTED line total (unit price * quantity), in dollars.
- region:   2-letter region code of the customer (e.g. "TX"), or None for an
            unknown customer (pays 0 tax).
- discount: customer discount as a fraction (0.10 = 10%). Applied here, once,
            to the taxable amount.

Returns the total sales tax in dollars, rounded to the cent (half up).

Rules (data_tax/RULES.md):
- Tax percent depends on the region (rates.csv, percent numbers e.g. 8.25).
- Items whose category is in exempt_categories.csv are not taxed.
- base = taxable_amount * (1 - discount)
- tax  = base * tax_pct / 100, rounded to the cent (half up).
- Unknown customer (region None) pays 0%.
"""

import csv
from decimal import Decimal, ROUND_HALF_UP
from functools import lru_cache
from pathlib import Path

_DATA_DIR = Path(__file__).resolve().parent / "data_tax"
_CENT = Decimal("0.01")
_HUNDRED = Decimal("100")


@lru_cache(maxsize=None)
def _load_rates() -> dict:
    """Region code -> tax percent as an exact Decimal (e.g. 'TX' -> Decimal('8.25'))."""
    rates = {}
    with open(_DATA_DIR / "rates.csv", newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            rates[row["region"].strip()] = Decimal(row["tax_pct"].strip())
    return rates


@lru_cache(maxsize=None)
def _load_exempt_categories() -> frozenset:
    """Normalized category names that are not taxed."""
    with open(_DATA_DIR / "exempt_categories.csv", newline="", encoding="utf-8") as f:
        return frozenset(
            row["category"].strip().lower()
            for row in csv.DictReader(f)
            if row.get("category") and row["category"].strip()
        )


def tax_percent(region: str) -> Decimal:
    """Tax percent for a region code. Raises KeyError if the region is unknown."""
    rates = _load_rates()
    if region not in rates:
        raise KeyError(f"no tax rate for region {region!r}")
    return rates[region]


def is_exempt(category: str) -> bool:
    """True if items in this category are not taxed."""
    return str(category).strip().lower() in _load_exempt_categories()


def calculate_tax(lines: list, region, discount: float = 0.0) -> float:
    """Total sales tax for an order, in dollars, rounded to the cent (half up).

    lines:    list of {"category": str, "amount": float}; amount is undiscounted
              (unit price * quantity), in dollars.
    region:   customer region code, or None for an unknown customer (0 tax).
    discount: customer discount fraction (0.10 = 10%), applied to the taxable amount.
    """
    if not 0 <= discount <= 1:
        raise ValueError(f"discount must be a fraction between 0 and 1, got {discount!r}")

    # Use Decimal built from the printed value so 12.5 means exactly 12.50
    # and half-cent cases are rounded correctly.
    taxable = Decimal("0")
    for line in lines:
        if not is_exempt(line["category"]):
            taxable += Decimal(str(line["amount"]))

    base = taxable * (Decimal("1") - Decimal(str(discount)))

    if region is None:  # unknown customer pays 0% tax
        rate = Decimal("0")
    else:
        rate = tax_percent(region)

    tax = (base * rate / _HUNDRED).quantize(_CENT, rounding=ROUND_HALF_UP)
    return float(tax)
