"""Sales tax rules for the invoicing package (owned by agent2).

Agreed interface (decision log topic: tax.interface, plus the shared
conventions money_and_lookup_conventions v2):

- All money is integer cents (1250 = $12.50).
- All percents are plain numbers (10 = 10%, 8.25 = 8.25%).
- compute_tax(region, lines, discount_pct) -> int cents
    region:       customer region key from data_tax/rates.csv, or None when
                  the customer is unknown (-> 0 tax, per RULES.md).
                  An unknown non-None region raises KeyError.
    lines:        iterable of {"category": str, "amount_cents": int}
    discount_pct: number in 0..100 (0 = no discount)
- tax_pct(region) -> Decimal percent for the region (None -> 0).
- is_exempt(category) -> bool.

Rules (data_tax/RULES.md):
    taxable = sum of amount_cents of lines whose category is NOT exempt
    base    = taxable * (100 - discount_pct) / 100
    tax     = base * tax_pct / 100, rounded half up to the cent (once, at the end)

All arithmetic is done with Decimal (never float) so that no binary
rounding error can change a cent.
"""

from __future__ import annotations

import csv
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Iterable, Mapping, Optional, Union

_DATA_DIR = Path(__file__).resolve().parent / "data_tax"
_RATES_FILE = _DATA_DIR / "rates.csv"
_EXEMPT_FILE = _DATA_DIR / "exempt_categories.csv"

_ZERO = Decimal("0")
_HUNDRED = Decimal("100")
_CENT = Decimal("1")


def _norm(text: str) -> str:
    return text.strip().lower()


def _load_rates(path: Path) -> dict[str, Decimal]:
    rates: dict[str, Decimal] = {}
    with path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            region = _norm(row["region"]).upper()
            rates[region] = Decimal(row["tax_pct"].strip())
    return rates


def _load_exempt(path: Path) -> frozenset[str]:
    with path.open(newline="", encoding="utf-8") as f:
        return frozenset(
            _norm(row["category"]) for row in csv.DictReader(f) if row["category"].strip()
        )


_RATES: dict[str, Decimal] = _load_rates(_RATES_FILE)
_EXEMPT: frozenset[str] = _load_exempt(_EXEMPT_FILE)


def _rate_for(region: Optional[str]) -> Decimal:
    """Return the tax percent for a region. None (unknown customer) -> 0.

    Raises KeyError for a region string that is not in rates.csv.
    """
    if region is None:
        return _ZERO
    key = _norm(region).upper()
    if key not in _RATES:
        raise KeyError(f"unknown tax region: {region!r}")
    return _RATES[key]


def tax_pct(region: Optional[str]) -> Decimal:
    """Tax percent for the region, e.g. Decimal('8.25') for TX.

    None (unknown customer) -> Decimal('0'). Unknown region -> KeyError.
    """
    return _rate_for(region)


def is_exempt(category: str) -> bool:
    """True if the item category is listed in exempt_categories.csv."""
    return _norm(category) in _EXEMPT


def compute_tax(
    region: Optional[str],
    lines: Iterable[Mapping[str, object]],
    discount_pct: Union[int, float, str, Decimal],
) -> int:
    """Return the sales tax for an order, in integer cents.

    region:       customer region key, or None for an unknown customer (0 tax).
    lines:        iterable of {"category": str, "amount_cents": int}.
    discount_pct: customer discount as a percent number (0..100).
    """
    rate = _rate_for(region)  # validates region first (KeyError if unknown)

    discount = Decimal(str(discount_pct))
    if not (_ZERO <= discount <= _HUNDRED):
        raise ValueError(f"discount_pct must be in 0..100, got {discount_pct!r}")

    taxable_cents = 0
    for line in lines:
        if is_exempt(str(line["category"])):
            continue
        amount = line["amount_cents"]
        if not isinstance(amount, int) or isinstance(amount, bool):
            raise TypeError(f"amount_cents must be int, got {amount!r}")
        taxable_cents += amount

    if rate == _ZERO or taxable_cents == 0:
        return 0

    # base = taxable * (100 - discount) / 100 ; tax = base * rate / 100
    base = Decimal(taxable_cents) * (_HUNDRED - discount) / _HUNDRED
    tax = base * rate / _HUNDRED
    return int(tax.quantize(_CENT, rounding=ROUND_HALF_UP))
