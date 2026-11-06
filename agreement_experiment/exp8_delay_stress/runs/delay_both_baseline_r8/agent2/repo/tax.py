"""Tax module. Owned by agent2. Computes sales tax.

The data files and rules are in data_tax/ next to this file:
  - data_tax/rates.csv              region,tax_pct
  - data_tax/exempt_categories.csv  category
  - data_tax/RULES.md               the rules this module implements

Public API (agreed with agent3, invoice.py):

  calculate(region, discount_multiplier, lines) -> (tax_amount, tax_rate_multiplier)

    region              : str customer region (e.g. "TX"), or None for an unknown
                          customer (-> (Decimal('0.00'), Decimal('1'))).
                          A region string not in rates.csv raises KeyError.
    discount_multiplier : Decimal, 0.90 for 10% off, Decimal('1') for no discount.
    lines               : list of (category: str, line_amount: Decimal) for the
                          order's lines, in dollars, before discount.
    tax_amount          : Decimal dollars, rounded to the cent (half up).
    tax_rate_multiplier : Decimal, 1 + tax_pct/100, e.g. Decimal('1.0825');
                          Decimal('1') when no tax applies.

Rules (RULES.md):
  taxable = sum of line amounts whose category is NOT in exempt_categories.csv
  base    = taxable * discount_multiplier
  tax     = base * tax_pct / 100, rounded to the cent (half up)
"""

import csv
import os
from decimal import Decimal, ROUND_HALF_UP

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_tax")
_RATES_PATH = os.path.join(_DATA_DIR, "rates.csv")
_EXEMPT_PATH = os.path.join(_DATA_DIR, "exempt_categories.csv")

_CENT = Decimal("0.01")
_HUNDRED = Decimal(100)


def _load_rates(path):
    rates = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            region = (row.get("region") or "").strip()
            if region:
                # Decimal(str) keeps values such as 8.875 exact.
                rates[region] = Decimal((row.get("tax_pct") or "0").strip())
    return rates


def _load_exempt(path):
    exempt = set()
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            category = (row.get("category") or "").strip().lower()
            if category:
                exempt.add(category)
    return frozenset(exempt)


_RATES = _load_rates(_RATES_PATH)
_EXEMPT = _load_exempt(_EXEMPT_PATH)


def tax_rate_pct(region):
    """Tax percent for a region (e.g. Decimal('8.25')). KeyError if region is unknown."""
    key = region.strip()
    if key not in _RATES:
        raise KeyError(f"no tax rate for region {region!r}")
    return _RATES[key]


def is_exempt(category):
    """True if this category is not taxed. Case-insensitive; unlisted categories are taxable."""
    return category.strip().lower() in _EXEMPT


def _to_decimal(value, name):
    if isinstance(value, bool):
        raise TypeError(f"{name} must be a number, got {value!r}")
    if isinstance(value, Decimal):
        return value
    if isinstance(value, (int, str)):
        return Decimal(value)
    if isinstance(value, float):
        return Decimal(str(value))
    raise TypeError(f"{name} must be a number, got {value!r}")


def calculate(region, discount_multiplier, lines):
    """Return (tax_amount, tax_rate_multiplier) for one order. See module docstring."""
    if region is None:
        # Unknown customer pays 0% tax (RULES.md).
        return Decimal("0.00"), Decimal("1")

    rate = tax_rate_pct(region)  # KeyError on unknown region
    multiplier = _to_decimal(discount_multiplier, "discount_multiplier")
    if multiplier < 0 or multiplier > 1:
        raise ValueError(f"discount_multiplier must be between 0 and 1, got {multiplier}")

    taxable = Decimal("0")
    for category, amount in lines:
        if not is_exempt(category):
            taxable += _to_decimal(amount, "line_amount")

    base = taxable * multiplier
    tax = (base * rate / _HUNDRED).quantize(_CENT, rounding=ROUND_HALF_UP)
    rate_multiplier = Decimal("1") + rate / _HUNDRED
    return tax, rate_multiplier
