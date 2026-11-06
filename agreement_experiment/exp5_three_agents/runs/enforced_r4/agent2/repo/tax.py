"""Sales tax calculation for the invoicing package.

Contract (committed team decision ``tax_api`` v2):

- ``calculate_tax(lines, region) -> int``
    ``lines`` is an iterable of ``(category, amount_cents)`` pairs, one per
    known invoice line. ``amount_cents`` is the *already discounted* line
    amount in integer cents (the caller applies the customer discount via
    ``pricing.discounted_price_cents``). Lines whose category is listed in
    ``data_tax/exempt_categories.csv`` are excluded from the taxable base.
    The return value is the tax amount in integer cents, rounded half up.
- ``get_rate_percent(region) -> Decimal``
    The tax percent for ``region`` (e.g. ``Decimal("8.25")``). Returns
    ``Decimal(0)`` for ``None`` or an unknown region.

Money is never a float. Rates come from ``data_tax/rates.csv`` and exempt
categories from ``data_tax/exempt_categories.csv``; both are loaded relative
to this module's file.

Known deviation (recorded in the decision log): ``data_tax/RULES.md`` applies
the customer discount to the summed taxable base. The agreed contract
discounts each line before tax, which can differ by at most one cent from
that because of per-line rounding.
"""

import csv
import os
from decimal import Decimal, ROUND_HALF_UP

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_tax")
_RATES_PATH = os.path.join(_DATA_DIR, "rates.csv")
_EXEMPT_PATH = os.path.join(_DATA_DIR, "exempt_categories.csv")


def _normalize(value):
    return value.strip().upper()


def _load_rates(path):
    rates = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            region = _normalize(row["region"])
            if region:
                rates[region] = Decimal(row["tax_pct"].strip())
    return rates


def _load_exempt(path):
    exempt = set()
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            category = row["category"].strip().lower()
            if category:
                exempt.add(category)
    return exempt


_RATES = _load_rates(_RATES_PATH)
_EXEMPT = _load_exempt(_EXEMPT_PATH)


def get_rate_percent(region):
    """Return the tax percent for ``region`` as a Decimal.

    Returns ``Decimal(0)`` when ``region`` is ``None`` or not in rates.csv.
    """
    if not isinstance(region, str):
        return Decimal(0)
    return _RATES.get(_normalize(region), Decimal(0))


def is_exempt(category):
    """Return True if items in ``category`` are not taxed."""
    if not isinstance(category, str):
        raise TypeError("category must be str")
    return category.strip().lower() in _EXEMPT


def calculate_tax(lines, region):
    """Return the sales tax in integer cents for the given invoice lines.

    ``lines``: iterable of ``(category: str, amount_cents: int)``.
    ``region``: state code such as ``"TX"``; ``None`` or unknown means 0%.

    Raises TypeError for invalid input types. Unknown categories or regions
    do not raise.
    """
    taxable_cents = 0
    for line in lines:
        try:
            category, amount_cents = line
        except (TypeError, ValueError):
            raise TypeError("each line must be a (category, amount_cents) pair")
        if not isinstance(category, str):
            raise TypeError("category must be str")
        if isinstance(amount_cents, bool) or not isinstance(amount_cents, int):
            raise TypeError("amount_cents must be int")
        if not is_exempt(category):
            taxable_cents += amount_cents

    rate = get_rate_percent(region)
    tax = (Decimal(taxable_cents) * rate / Decimal(100)).quantize(
        Decimal(1), rounding=ROUND_HALF_UP
    )
    return int(tax)
