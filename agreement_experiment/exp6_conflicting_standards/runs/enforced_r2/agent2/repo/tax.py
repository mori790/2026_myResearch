"""Tax module. Owned by agent2. Computes sales tax. The data files and rules are in data_tax/ next to this file.

Committed boundary (decision log topic ``tax_api`` v2):
    get_tax(region, lines, discount) -> [tax_amount, tax_rate]
- region:   customer region code from pricing.get_customer (e.g. "TX"), or None
            for an unknown customer (0 tax). A region with no rate in rates.csv
            raises KeyError (data error).
- lines:    list of [category, line_amount] for ALL items, including exempt ones.
            category comes from pricing.get_item; line_amount is the pre-discount
            line amount in dollars (float).
- discount: customer discount as a fraction (0.10 = 10%); 0 if unknown.
- returns:  tax_amount in dollars (float, rounded to the cent, half up) and
            tax_rate as a fraction (0.0825 for 8.25%; 0 for no tax).

Internal convention (team standard): money is handled as integer cents and
percentages as percent numbers. Conversion happens only at the boundary.

Rules (data_tax/RULES.md):
    taxable_cents = sum of line amounts whose category is NOT exempt
    base          = taxable_cents * (100 - discount_pct) / 100
    tax           = round_half_up(base * tax_pct / 100)   (single rounding, on the total)
"""

import csv
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path
from typing import Iterable, Optional, Sequence, Set

_DATA_DIR = Path(__file__).resolve().parent / "data_tax"
_RATES_FILE = _DATA_DIR / "rates.csv"
_EXEMPT_FILE = _DATA_DIR / "exempt_categories.csv"

_HUNDRED = Decimal(100)
_ONE_CENT = Decimal(1)


def _key(value) -> str:
    return str(value).strip().casefold()


def _load_rates(path: Path) -> dict:
    """region key -> tax percent (Decimal, e.g. Decimal('8.25'))."""
    rates = {}
    with path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            region = _key(row["region"])
            if region:
                rates[region] = Decimal(row["tax_pct"].strip())
    return rates


def _load_exempt(path: Path) -> Set[str]:
    exempt = set()
    with path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            category = _key(row["category"])
            if category:
                exempt.add(category)
    return exempt


_RATES = _load_rates(_RATES_FILE)
_EXEMPT_CATEGORIES = _load_exempt(_EXEMPT_FILE)


def tax_percent(region: str) -> Decimal:
    """Tax percent for a region (e.g. Decimal('8.25')). KeyError if the region has no rate."""
    key = _key(region)
    if key not in _RATES:
        raise KeyError(f"no tax rate for region {region!r}")
    return _RATES[key]


def is_exempt(category: str) -> bool:
    """True if items in this category are not taxed."""
    return _key(category) in _EXEMPT_CATEGORIES


def _to_cents(amount) -> int:
    """Dollars (float/int/str) -> integer cents, rounded half up to the cent."""
    if isinstance(amount, bool):
        raise ValueError(f"amount must be a number, got {amount!r}")
    d = Decimal(str(amount))
    if not d.is_finite() or d < 0:
        raise ValueError(f"amount must be a finite non-negative number, got {amount!r}")
    return int((d * _HUNDRED).quantize(_ONE_CENT, rounding=ROUND_HALF_UP))


def _to_fraction(value, name: str) -> Decimal:
    if isinstance(value, bool):
        raise ValueError(f"{name} must be a number, got {value!r}")
    d = Decimal(str(value))
    if not d.is_finite() or d < 0 or d > 1:
        raise ValueError(f"{name} must be a fraction between 0 and 1, got {value!r}")
    return d


def get_tax(region: Optional[str], lines: Iterable[Sequence], discount: float = 0):
    """Return ``[tax_amount, tax_rate]`` for one order (see the module docstring).

    region=None (unknown customer) gives ``[0.0, 0.0]``.
    """
    discount_fraction = _to_fraction(discount, "discount")

    taxable_cents = 0
    for line in lines:
        category, amount = line[0], line[1]
        if not is_exempt(category):
            taxable_cents += _to_cents(amount)

    if region is None:
        return [0.0, 0.0]

    tax_pct = tax_percent(region)  # KeyError for an unknown region
    base_cents = Decimal(taxable_cents) * (_HUNDRED - discount_fraction * _HUNDRED) / _HUNDRED
    tax_cents = (base_cents * tax_pct / _HUNDRED).quantize(_ONE_CENT, rounding=ROUND_HALF_UP)

    tax_amount = float(Decimal(int(tax_cents)) / _HUNDRED)
    tax_rate = float(tax_pct / _HUNDRED)
    return [tax_amount, tax_rate]
