"""Tax module. Owned by agent2. Computes sales tax.

The data files and rules are in data_tax/ next to this file.

Units (team standard):
  - money: integer cents (1250 means $12.50)
  - percentages: percent numbers (10 means 10%, 8.25 means 8.25%)
  - a lookup that finds nothing raises KeyError (except None region -> 0% tax)

Public API (agreed in topic `tax_api`):
  calculate_tax(lines, region, discount_pct=0) -> int (tax in cents)
  tax_rate(region) -> float (percent)
  is_exempt(category) -> bool
"""

import csv
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

_DATA_DIR = Path(__file__).resolve().parent / "data_tax"
_RATES_FILE = _DATA_DIR / "rates.csv"
_EXEMPT_FILE = _DATA_DIR / "exempt_categories.csv"


def _load_rates(path):
    rates = {}
    with path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            region = (row.get("region") or "").strip()
            pct = (row.get("tax_pct") or "").strip()
            if region and pct:
                rates[region] = Decimal(pct)  # exact; percent number
    return rates


def _load_exempt(path):
    exempt = set()
    with path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            category = (row.get("category") or "").strip()
            if category:
                exempt.add(category)
    return frozenset(exempt)


_RATES = _load_rates(_RATES_FILE)
_EXEMPT = _load_exempt(_EXEMPT_FILE)


def is_exempt(category):
    """True if items of this category are not taxed (exempt_categories.csv)."""
    return category in _EXEMPT


def _rate_decimal(region):
    """Exact Decimal percent for a region. None -> 0. Unknown region -> KeyError."""
    if region is None:
        return Decimal(0)
    if region not in _RATES:
        raise KeyError(f"unknown tax region: {region!r}")
    return _RATES[region]


def tax_rate(region):
    """Sales tax rate for a region, as a percent number (8.25 means 8.25%).

    None (unknown customer) -> 0.0. A region not in rates.csv -> KeyError.
    """
    return float(_rate_decimal(region))


def _to_decimal_discount(discount_pct):
    if isinstance(discount_pct, bool) or not isinstance(discount_pct, (int, float, Decimal)):
        raise TypeError(f"discount_pct must be a number, got {type(discount_pct).__name__}")
    # str() avoids binary-float artifacts such as 0.1 -> 0.1000000000000000055...
    d = Decimal(str(discount_pct))
    if d < 0 or d > 100:
        raise ValueError(f"discount_pct must be between 0 and 100, got {discount_pct}")
    return d


def calculate_tax(lines, region, discount_pct=0):
    """Return the sales tax for an order, in integer cents.

    lines: iterable of {"category": str, "amount_cents": int}, one per order line.
        amount_cents is the line total BEFORE tax and BEFORE the customer discount.
    region: customer region (e.g. "TX"), or None for an unknown customer -> 0.
    discount_pct: customer discount in percent numbers (10 means 10%).

    Rules (data_tax/RULES.md):
        taxable = sum of amount_cents for lines whose category is not exempt
        base    = taxable * (100 - discount_pct) / 100
        tax     = base * tax_pct / 100, rounded to the cent (half up)
    Only the final tax is rounded; all intermediate math is exact Decimal.
    Raises KeyError if region is not in rates.csv.
    """
    discount = _to_decimal_discount(discount_pct)

    taxable_cents = 0
    for line in lines:
        amount = line["amount_cents"]
        if isinstance(amount, bool) or not isinstance(amount, int):
            raise TypeError(
                f"amount_cents must be an int (cents), got {type(amount).__name__}: {amount!r}"
            )
        if not is_exempt(line["category"]):
            taxable_cents += amount

    rate_pct = _rate_decimal(region)  # KeyError for unknown region
    if rate_pct == 0 or taxable_cents == 0:
        return 0

    # taxable * (100 - d)/100 * rate/100  ==  taxable * (100 - d) * rate / 10000
    # Dividing by 10000 is exact in decimal, so no rounding happens before the end.
    raw_tax = Decimal(taxable_cents) * (Decimal(100) - discount) * rate_pct / Decimal(10000)
    return int(raw_tax.quantize(Decimal("1"), rounding=ROUND_HALF_UP))
