"""Sales tax calculation (owned by agent2).

Committed interface (decision ``tax_api`` v2):

* Money is integer cents everywhere.
* ``compute_tax(lines, region, discount_pct) -> int``
    Returns the tax in cents only (not the total).
* ``tax_rate_percent(region) -> Decimal``
    Returns the tax percent for a region, e.g. ``Decimal("8.25")`` for TX.

Rules (data_tax/RULES.md):

* The tax percent depends on the customer's region (data_tax/rates.csv).
* Items whose category is listed in data_tax/exempt_categories.csv are not taxed.
* base = taxable_amount * (100 - discount_pct) / 100
* tax  = base * tax_pct / 100, rounded to the cent (half up).
* An unknown customer / region pays 0% tax.
"""

from __future__ import annotations

import csv
import os
from decimal import Decimal, ROUND_HALF_UP
from typing import Iterable, Optional, Tuple, Union

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_tax")
_RATES_PATH = os.path.join(_DATA_DIR, "rates.csv")
_EXEMPT_PATH = os.path.join(_DATA_DIR, "exempt_categories.csv")

_HUNDRED = Decimal(100)


def _load_rates(path: str) -> dict:
    rates = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            region = (row.get("region") or "").strip()
            pct = (row.get("tax_pct") or "").strip()
            if region and pct:
                rates[region] = Decimal(pct)
    return rates


def _load_exempt(path: str) -> frozenset:
    exempt = set()
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            category = (row.get("category") or "").strip().lower()
            if category:
                exempt.add(category)
    return frozenset(exempt)


_RATES = _load_rates(_RATES_PATH)
_EXEMPT_CATEGORIES = _load_exempt(_EXEMPT_PATH)


def _normalize_region(region: Optional[str]) -> Optional[str]:
    if region is None:
        return None
    region = str(region).strip()
    return region or None


def tax_rate_percent(region: Optional[str]) -> Decimal:
    """Return the sales tax percent for ``region`` (0 if None or unknown)."""
    key = _normalize_region(region)
    if key is None:
        return Decimal(0)
    return _RATES.get(key, Decimal(0))


def _to_decimal_pct(discount_pct: Union[int, float, str, Decimal, None]) -> Decimal:
    if discount_pct is None:
        return Decimal(0)
    # Go through str() so that floats such as 10.0 do not carry binary noise.
    value = Decimal(str(discount_pct))
    if not (Decimal(0) <= value <= _HUNDRED):
        raise ValueError(f"discount_pct must be between 0 and 100, got {discount_pct!r}")
    return value


def compute_tax(
    lines: Iterable[Tuple[str, int]],
    region: Optional[str],
    discount_pct: Union[int, float, str, Decimal, None],
) -> int:
    """Compute the sales tax for an invoice, in integer cents.

    Args:
        lines: iterable of ``(category, amount_cents)`` pairs. ``amount_cents``
            is the pre-discount line total (quantity * unit price) in cents.
            Lines whose category is exempt are excluded from the taxable base.
        region: customer region code such as ``"TX"``, or ``None``.
            Unknown or ``None`` regions pay 0% tax.
        discount_pct: customer discount percent, 0..100 (0 if none).

    Returns:
        The tax amount in cents (not the total). The base is not rounded;
        only the final tax is rounded, half up, to the cent.
    """
    taxable_cents = 0
    for category, amount_cents in lines:
        if isinstance(amount_cents, bool) or not isinstance(amount_cents, int):
            raise TypeError(f"amount_cents must be int, got {amount_cents!r}")
        key = (str(category).strip().lower() if category is not None else "")
        if key in _EXEMPT_CATEGORIES:
            continue
        taxable_cents += amount_cents

    rate = tax_rate_percent(region)
    if rate == 0 or taxable_cents == 0:
        return 0

    discount = _to_decimal_pct(discount_pct)
    base = Decimal(taxable_cents) * (_HUNDRED - discount) / _HUNDRED  # cents, exact
    tax = base * rate / _HUNDRED  # cents, exact
    return int(tax.quantize(Decimal(1), rounding=ROUND_HALF_UP))
