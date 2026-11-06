"""Tax module. Owned by agent2. Computes sales tax. The data files and rules are in data_tax/ next to this file.

Public API (all money in integer cents, all percentages as percent numbers):

    tax_pct(region)                          -> Decimal   tax rate for a region
    compute_tax(lines, region, discount_pct) -> int       tax in cents
    compute_tax_details(lines, region, discount_pct) -> TaxResult

`lines` is an iterable of (category, amount_cents) pairs, or mappings with
keys "category" and "amount_cents". Lines whose category is listed in
exempt_categories.csv are not taxed.

Rules (data_tax/RULES.md):
    taxable   = sum of amount_cents over non-exempt lines
    base      = taxable * (100 - discount_pct) / 100
    tax       = base * tax_pct / 100, rounded to the cent, half up
    unknown customer (region is None or empty) pays 0%
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path
from typing import Iterable, Mapping, Optional, Tuple, Union

_DATA_DIR = Path(__file__).resolve().parent / "data_tax"


def _load_rates(path: Path) -> dict:
    rates = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            region = row["region"].strip().upper()
            rates[region] = Decimal(row["tax_pct"].strip())
    return rates


def _load_exempt(path: Path) -> frozenset:
    exempt = set()
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            exempt.add(row["category"].strip().lower())
    return frozenset(exempt)


_RATES = _load_rates(_DATA_DIR / "rates.csv")
_EXEMPT = _load_exempt(_DATA_DIR / "exempt_categories.csv")

LineItem = Union[Tuple[str, int], Mapping[str, object]]


@dataclass(frozen=True)
class TaxResult:
    taxable_cents: int   # sum of non-exempt line amounts, before discount
    tax_pct: Decimal     # rate applied (percent number)
    tax_cents: int       # final tax in cents, rounded half up


def _is_exempt(category: str) -> bool:
    return category.strip().lower() in _EXEMPT


def tax_pct(region: Optional[str]) -> Decimal:
    """Return the tax percent for a customer region.

    None or an empty region means an unknown customer, which pays 0%.
    A region that is given but not in rates.csv raises KeyError.
    """
    if region is None or not str(region).strip():
        return Decimal("0")
    key = str(region).strip().upper()
    if key not in _RATES:
        raise KeyError(f"no tax rate for region {region!r}")
    return _RATES[key]


def _iter_lines(lines: Iterable[LineItem]):
    for line in lines:
        if isinstance(line, Mapping):
            category = line["category"]
            amount = line["amount_cents"]
        else:
            category, amount = line
        if isinstance(amount, bool) or not isinstance(amount, int):
            raise TypeError(f"amount_cents must be int, got {amount!r}")
        if amount < 0:
            raise ValueError(f"amount_cents must be >= 0, got {amount}")
        yield str(category), amount


def compute_tax_details(
    lines: Iterable[LineItem],
    region: Optional[str],
    discount_pct: Union[int, float, str, Decimal] = 0,
) -> TaxResult:
    """Compute tax for an order. Returns taxable subtotal, rate and tax in cents."""
    discount = Decimal(str(discount_pct))
    if discount < 0 or discount > 100:
        raise ValueError(f"discount_pct must be in [0, 100], got {discount_pct}")

    taxable = 0
    for category, amount in _iter_lines(lines):
        if not _is_exempt(category):
            taxable += amount

    rate = tax_pct(region)
    base = Decimal(taxable) * (Decimal(100) - discount) / Decimal(100)
    tax = base * rate / Decimal(100)
    tax_cents = int(tax.quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    return TaxResult(taxable_cents=taxable, tax_pct=rate, tax_cents=tax_cents)


def compute_tax(
    lines: Iterable[LineItem],
    region: Optional[str],
    discount_pct: Union[int, float, str, Decimal] = 0,
) -> int:
    """Return the sales tax for an order in integer cents."""
    return compute_tax_details(lines, region, discount_pct).tax_cents
