"""Tax module. Owned by agent2. Computes sales tax.

The data files and rules are in data_tax/ next to this file (see data_tax/RULES.md).

Conventions (team decisions, see agreement log topics pricing_api v2 and tax_api v3):
- Money amounts are integers in cents (1250 means $12.50).
- Percentages are percent numbers (10 means 10%, 8.25 means 8.25%).
- A lookup that finds nothing raises KeyError (unknown region string).
  region=None means an unknown customer, who pays 0% tax (RULES.md).

Public API (tax_api v3):
- compute_tax(lines, region, discount_pct=0) -> TaxResult
- tax_rate(region) -> Decimal          (percent number; None -> 0)
- is_exempt(category) -> bool
"""

from __future__ import annotations

import csv
import os
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from typing import Iterable, Mapping, Optional, Union

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_tax")
_RATES_PATH = os.path.join(_DATA_DIR, "rates.csv")
_EXEMPT_PATH = os.path.join(_DATA_DIR, "exempt_categories.csv")


def _load_rates(path: str) -> dict:
    rates = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            region = row["region"].strip()
            # Decimal from the text in the file keeps values like 8.875 exact.
            rates[region] = Decimal(row["tax_pct"].strip())
    return rates


def _load_exempt(path: str) -> frozenset:
    with open(path, newline="", encoding="utf-8") as f:
        return frozenset(
            row["category"].strip().lower()
            for row in csv.DictReader(f)
            if row.get("category") and row["category"].strip()
        )


_RATES = _load_rates(_RATES_PATH)
_EXEMPT_CATEGORIES = _load_exempt(_EXEMPT_PATH)


@dataclass(frozen=True)
class TaxResult:
    """Result of a tax computation.

    taxable_cents: sum of the non-exempt line amounts, before the discount (cents).
    discount_pct:  discount that was applied (percent number, Decimal).
    tax_pct:       tax rate that was applied (percent number, Decimal).
    tax_cents:     tax amount in cents, rounded half up to the cent.
    """

    taxable_cents: int
    discount_pct: Decimal
    tax_pct: Decimal
    tax_cents: int


def is_exempt(category: str) -> bool:
    """True if items in this category are not taxed (see exempt_categories.csv)."""
    return category.strip().lower() in _EXEMPT_CATEGORIES


def tax_rate(region: Optional[str]) -> Decimal:
    """Tax percent for a customer's region (rates.csv).

    region=None means an unknown customer, who pays 0% tax (RULES.md).
    An unknown region string raises KeyError.
    """
    if region is None:
        return Decimal("0")
    return _RATES[region.strip()]


LineLike = Mapping[str, Union[int, str]]


def compute_tax(
    lines: Iterable[LineLike],
    region: Optional[str],
    discount_pct: Union[int, float, str, Decimal] = 0,
) -> TaxResult:
    """Compute sales tax for one order.

    lines: iterable of mappings with keys
        "amount_cents" (int, line total before discount, in cents) and
        "category"     (str, item category).
        Lines whose category is exempt are not taxed. Pass known items only.
    region: customer's region code (e.g. "TX"), or None for an unknown customer.
    discount_pct: customer's discount as a percent number (e.g. 10 for 10%).

    Rule (RULES.md):
        base = taxable_amount * (100 - discount_pct) / 100
        tax  = base * tax_pct / 100, rounded to the cent (half up)
    The discount applies only to the taxable (non-exempt) lines.
    """
    taxable_cents = 0
    for line in lines:
        amount = line["amount_cents"]
        if not isinstance(amount, int) or isinstance(amount, bool):
            raise TypeError("amount_cents must be an int (cents)")
        if not is_exempt(str(line["category"])):
            taxable_cents += amount

    discount = Decimal(str(discount_pct))
    if discount < 0 or discount > 100:
        raise ValueError("discount_pct must be between 0 and 100")

    rate = tax_rate(region)

    base = Decimal(taxable_cents) * (Decimal(100) - discount) / Decimal(100)
    tax = base * rate / Decimal(100)
    tax_cents = int(tax.quantize(Decimal("1"), rounding=ROUND_HALF_UP))

    return TaxResult(
        taxable_cents=taxable_cents,
        discount_pct=discount,
        tax_pct=rate,
        tax_cents=tax_cents,
    )
