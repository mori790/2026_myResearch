"""Tax module. Owned by agent2. Computes sales tax. The data files and rules are in data_tax/ next to this file.

Interface (agreed with agent1 / agent3, see shared agreement log):

    tax_rate(region) -> Decimal
        Tax percent for a region code, e.g. "TX" -> Decimal("8.25").
        region None (unknown customer) -> Decimal("0").
        Unknown region code -> KeyError.

    is_exempt(category) -> bool
        True if the item category is listed in exempt_categories.csv.

    compute_tax(region, lines, discount_pct=0) -> int
        region:       customer's region code, or None for an unknown customer (0% tax).
        lines:        iterable of (amount_cents: int, category: str), one per line item.
        discount_pct: customer's discount in percent (10 means 10%).
        Returns the tax in integer cents.

Percentages are percent numbers (8.25 means 8.25%). Money is integer cents.
"""

import csv
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Iterable, Optional, Tuple

_DATA_DIR = Path(__file__).resolve().parent / "data_tax"


def _load_rates(path: Path) -> dict:
    rates = {}
    with path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            region = row["region"].strip()
            if not region:
                continue
            if region in rates:
                raise ValueError(f"duplicate region in {path.name}: {region}")
            rates[region] = Decimal(row["tax_pct"].strip())
    return rates


def _load_exempt(path: Path) -> frozenset:
    with path.open(newline="", encoding="utf-8") as f:
        return frozenset(
            row["category"].strip().casefold()
            for row in csv.DictReader(f)
            if row["category"].strip()
        )


_RATES = _load_rates(_DATA_DIR / "rates.csv")
_EXEMPT = _load_exempt(_DATA_DIR / "exempt_categories.csv")


def _to_decimal(value) -> Decimal:
    # Going through str() avoids binary float artifacts (8.875 stays exactly 8.875).
    return Decimal(str(value))


def tax_rate(region: Optional[str]) -> Decimal:
    """Return the tax percent for a region. None (unknown customer) gives 0."""
    if region is None:
        return Decimal("0")
    try:
        return _RATES[region.strip()]
    except KeyError:
        raise KeyError(f"no tax rate for region {region!r}") from None


def is_exempt(category: str) -> bool:
    """True if items in this category are not taxed."""
    return category.strip().casefold() in _EXEMPT


def compute_tax(
    region: Optional[str],
    lines: Iterable[Tuple[int, str]],
    discount_pct=0,
) -> int:
    """Return the sales tax in integer cents.

    Rules (data_tax/RULES.md):
      taxable = sum of amounts of non-exempt lines
      base    = taxable * (100 - discount_pct) / 100
      tax     = base * tax_pct / 100, rounded to the cent (half up)
    """
    taxable = 0
    for amount_cents, category in lines:
        if not isinstance(amount_cents, int):
            raise TypeError(f"amount must be int cents, got {amount_cents!r}")
        if not is_exempt(category):
            taxable += amount_cents

    discount = _to_decimal(discount_pct)
    if discount < 0 or discount > 100:
        raise ValueError(f"discount_pct must be in [0, 100], got {discount_pct!r}")

    pct = tax_rate(region)
    # Exact decimal arithmetic: taxable * (100 - d) * pct / (100 * 100).
    raw = Decimal(taxable) * (Decimal(100) - discount) * pct / Decimal(10000)
    return int(raw.quantize(Decimal("1"), rounding=ROUND_HALF_UP))
