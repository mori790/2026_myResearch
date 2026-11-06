"""Sales tax computation (owned by agent2).

Agreed API (tax.api v1, tax.unknown_customer v2, tax.money_units v2):

    compute_tax(region, discount_pct, lines) -> int   # tax in integer cents
    rate_for_region(region) -> float                  # percent number, e.g. 8.25

Conventions (team standard):
- Money amounts are integer cents (1250 == $12.50).
- Percentages are percent numbers (8.25 == 8.25%).
- A lookup that finds nothing raises KeyError.

Rules (data_tax/RULES.md):
- Tax rate depends on the customer's region (data_tax/rates.csv).
- Lines whose category is listed in data_tax/exempt_categories.csv are not taxed.
- base = taxable_amount * (100 - discount_pct) / 100
- tax  = base * tax_pct / 100, rounded to the cent (half up).
- Unknown customer (region None) pays 0% tax.

Arithmetic is done with decimal.Decimal; only the final tax is rounded.
"""

import csv
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

_DATA_DIR = Path(__file__).resolve().parent / "data_tax"
_RATES_FILE = _DATA_DIR / "rates.csv"
_EXEMPT_FILE = _DATA_DIR / "exempt_categories.csv"

_HUNDRED = Decimal(100)


def _load_rates(path: Path) -> dict:
    rates = {}
    with path.open(newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            region = row["region"].strip()
            rates[region] = Decimal(row["tax_pct"].strip())
    return rates


def _load_exempt(path: Path) -> frozenset:
    with path.open(newline="", encoding="utf-8-sig") as f:
        return frozenset(
            row["category"].strip() for row in csv.DictReader(f) if row["category"].strip()
        )


_RATES = _load_rates(_RATES_FILE)
_EXEMPT_CATEGORIES = _load_exempt(_EXEMPT_FILE)


def rate_for_region(region: str) -> float:
    """Return the tax rate for a region as a percent number (e.g. 8.25).

    Raises KeyError if the region is not in rates.csv (including None).
    """
    return float(_RATES[region])


def compute_tax(region, discount_pct, lines) -> int:
    """Return the sales tax for an order, in integer cents.

    region       -- region code such as "TX", or None for an unknown customer
                    (unknown customers pay 0 tax, no error).
    discount_pct -- customer discount as a percent number (0 if none).
    lines        -- iterable of dicts {"category": str, "amount_cents": int}.
                    Lines in an exempt category are excluded from the taxable sum.

    Raises KeyError if a non-None region is not in rates.csv.
    Raises ValueError for an out-of-range discount or a non-integer amount.
    """
    if region is None:
        return 0

    tax_pct = _RATES[region]  # KeyError for unknown region

    discount = Decimal(str(discount_pct))
    if not (Decimal(0) <= discount <= _HUNDRED):
        raise ValueError(f"discount_pct must be between 0 and 100, got {discount_pct!r}")

    taxable_cents = 0
    for line in lines:
        amount = line["amount_cents"]
        if isinstance(amount, bool) or not isinstance(amount, int):
            raise ValueError(f"amount_cents must be an int, got {amount!r}")
        if line["category"] in _EXEMPT_CATEGORIES:
            continue
        taxable_cents += amount

    # base = taxable * (100 - discount) / 100 ; tax = base * tax_pct / 100
    base = Decimal(taxable_cents) * (_HUNDRED - discount) / _HUNDRED
    tax = base * tax_pct / _HUNDRED

    return int(tax.quantize(Decimal(1), rounding=ROUND_HALF_UP))
