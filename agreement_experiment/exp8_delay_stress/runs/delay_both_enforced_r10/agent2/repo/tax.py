"""Sales tax module (owned by agent2).

Implements the committed team decisions:
  - TAX_API v3: tax_breakdown(region, lines, discount_rate) -> (rate, amount_cents)
  - MONEY_UNIT v4: all money amounts are integer cents.
  - PERCENT_REPR v2: rates and discount are Decimal fractions (0.10 = 10%).
  - TAX_UNKNOWN_REGION v1: region None -> 0% tax; unknown non-None region -> KeyError.

Tax rules (data_tax/RULES.md):
  taxable   = sum of line amounts whose category is NOT exempt
  base      = taxable * (1 - discount_rate)
  tax       = base * tax_rate, rounded to the cent (half up)
"""

import csv
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

_DATA_DIR = Path(__file__).resolve().parent / "data_tax"


def _load_rates(path):
    """Return {region: Decimal fraction} from rates.csv (tax_pct is a percent number)."""
    rates = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            region = row["region"].strip()
            pct = Decimal(row["tax_pct"].strip())
            rates[region] = pct / Decimal(100)  # percent -> fraction, exact in Decimal
    return rates


def _load_exempt(path):
    """Return the set of exempt category names from exempt_categories.csv."""
    with open(path, newline="", encoding="utf-8") as f:
        return {row["category"].strip() for row in csv.DictReader(f) if row["category"].strip()}


_RATES = _load_rates(_DATA_DIR / "rates.csv")
_EXEMPT = _load_exempt(_DATA_DIR / "exempt_categories.csv")

_CENT = Decimal("1")  # amounts are in integer cents, so rounding to 1 cent = rounding to an int


def _to_decimal_fraction(value):
    """Accept Decimal/int/float/str discount rates and return a Decimal fraction."""
    if isinstance(value, bool):
        raise TypeError("discount_rate must be a number, not bool")
    if isinstance(value, float):
        return Decimal(str(value))
    return Decimal(value)


def tax_breakdown(region, lines, discount_rate):
    """Compute sales tax for one customer's order.

    Args:
        region: customer region code as in data_tax/rates.csv (e.g. "TX"),
            or None for an unknown customer (0% tax).
        lines: iterable of (category, amount_cents) tuples, amount_cents is an
            int line total before discount and tax.
        discount_rate: Decimal fraction of the customer discount (0.10 = 10%),
            applied to the taxable base only.

    Returns:
        (rate, amount_cents): rate is a Decimal fraction (0.0825 = 8.25%, 0 if
        region is None); amount_cents is the tax as an int number of cents,
        rounded half up.

    Raises:
        KeyError: if region is not None and is not listed in rates.csv.
        TypeError/ValueError: on malformed input.
    """
    if region is None:
        rate = Decimal(0)
    else:
        if region not in _RATES:
            raise KeyError(f"unknown tax region: {region!r}")
        rate = _RATES[region]

    taxable_cents = 0
    for category, amount_cents in lines:
        if isinstance(amount_cents, bool) or not isinstance(amount_cents, int):
            raise TypeError(f"amount_cents must be int, got {type(amount_cents).__name__}")
        if category in _EXEMPT:
            continue
        taxable_cents += amount_cents

    discount = _to_decimal_fraction(discount_rate)
    if not (Decimal(0) <= discount <= Decimal(1)):
        raise ValueError(f"discount_rate must be a fraction in [0, 1], got {discount_rate!r}")

    base_cents = Decimal(taxable_cents) * (Decimal(1) - discount)
    tax_cents = (base_cents * rate).quantize(_CENT, rounding=ROUND_HALF_UP)
    return rate, int(tax_cents)
