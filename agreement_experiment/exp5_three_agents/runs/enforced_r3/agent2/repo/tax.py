"""Sales tax calculation.

Committed interface (TAX_API v2, MONEY_REPRESENTATION v2):

    compute(region, lines, discount_pm) -> (rate_pm, tax_cents)

Units (all integers, no floats):
    * money      : cents (USD). 1234 == $12.34
    * percents   : thousandths of a percent. 10% == 10000, 100% == 100000,
                   8.25% == 8250, 8.875% == 8875

Rules (data_tax/RULES.md):
    * The tax rate depends on the customer's region (data_tax/rates.csv).
    * Lines whose category is in data_tax/exempt_categories.csv are not taxed.
    * base = taxable_amount * (100 - discount_pct) / 100
    * tax  = base * tax_pct / 100, rounded to the cent (half up).
    * An unknown customer (region None / unknown) pays 0% tax.
"""

import csv
import os
from decimal import Decimal, ROUND_HALF_UP

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_tax")
_RATES_PATH = os.path.join(_DATA_DIR, "rates.csv")
_EXEMPT_PATH = os.path.join(_DATA_DIR, "exempt_categories.csv")

_PM_FULL = 100_000  # 100% in thousandths of a percent


def _percent_to_pm(text):
    """Convert a CSV percent string such as '8.875' to int thousandths (8875)."""
    value = Decimal(text.strip()) * 1000
    if value != value.to_integral_value():
        raise ValueError(f"percent {text!r} has more than 3 decimal places")
    return int(value)


def _load_rates(path=_RATES_PATH):
    rates = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            region = row["region"].strip().upper()
            rates[region] = _percent_to_pm(row["tax_pct"])
    return rates


def _load_exempt(path=_EXEMPT_PATH):
    with open(path, newline="", encoding="utf-8") as f:
        return {
            row["category"].strip().lower()
            for row in csv.DictReader(f)
            if row.get("category") and row["category"].strip()
        }


_RATES = _load_rates()
_EXEMPT = _load_exempt()


def rate_pm(region):
    """Return the tax rate in thousandths of a percent for a region.

    Unknown or None region -> 0 (no error).
    """
    if region is None:
        return 0
    return _RATES.get(str(region).strip().upper(), 0)


def is_exempt(category):
    """True if the category is listed in exempt_categories.csv."""
    if category is None:
        return False
    return str(category).strip().lower() in _EXEMPT


def _check_int(name, value):
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be int, got {type(value).__name__}")


def compute(region, lines, discount_pm):
    """Compute the sales tax for one order.

    Args:
        region: customer region code such as "TX", or None.
        lines: iterable of (category, amount_cents) pairs. amount_cents is the
            line total before discount and tax.
        discount_pm: customer discount in thousandths of a percent (10% = 10000).
            None is treated as 0.

    Returns:
        (rate_pm, tax_cents): the applied rate in thousandths of a percent and
        the total tax in integer cents, rounded once (half up) over the whole
        order. Returns (0, 0) when nothing is taxable or the region is unknown.
    """
    if discount_pm is None:
        discount_pm = 0
    _check_int("discount_pm", discount_pm)
    if not 0 <= discount_pm <= _PM_FULL:
        raise ValueError(f"discount_pm out of range: {discount_pm}")

    taxable_cents = 0
    for category, amount_cents in lines:
        _check_int("amount_cents", amount_cents)
        if amount_cents < 0:
            raise ValueError(f"amount_cents must be non-negative: {amount_cents}")
        if not is_exempt(category):
            taxable_cents += amount_cents

    rate = rate_pm(region)
    if taxable_cents == 0 or rate == 0:
        return (0, 0)  # committed contract: (0, 0) when nothing is taxable or region unknown

    # tax = taxable * (100000 - discount_pm)/100000 * rate/100000, in cents.
    # Keep the whole product in integers and round half up exactly once.
    numerator = taxable_cents * (_PM_FULL - discount_pm) * rate
    denominator = _PM_FULL * _PM_FULL
    tax_cents = (numerator + denominator // 2) // denominator
    return (rate, tax_cents)
