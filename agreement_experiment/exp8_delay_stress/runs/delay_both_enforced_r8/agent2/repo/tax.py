"""Tax module. Owned by agent2. Computes sales tax.

The data files and rules are in data_tax/ next to this file (see data_tax/RULES.md).

Interface (agreed in the shared decision log, topic "tax_api" v2):
    compute_tax(lines, region, discount_rate=0) -> TaxResult
        lines         : iterable of (category: str, amount_dollars) pairs, one per
                        invoice line, amount = unit_price * qty, BEFORE the customer
                        discount. Dollars as float or Decimal.
        region        : customer region code (e.g. "TX"), or None for an unknown
                        customer (pays 0% tax, no error).
        discount_rate : customer discount as a fraction (0.10 = 10% off); 0 if none.

    get_tax_rate(region) -> float   tax rate as a fraction (TX -> 0.0825). KeyError if unknown.
    is_exempt(category) -> bool     True if the category is listed in exempt_categories.csv.

Internal convention: all arithmetic is exact Decimal arithmetic on dollars;
the tax amount is rounded half up to the cent. Data files store percents
(rates.csv), which are converted to fractions here.
"""

import csv
import os
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Iterable, Optional, Tuple

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_tax")
_RATES_PATH = os.path.join(_DATA_DIR, "rates.csv")
_EXEMPT_PATH = os.path.join(_DATA_DIR, "exempt_categories.csv")

_CENT = Decimal("0.01")
_HUNDRED = Decimal(100)


def _norm(text: str) -> str:
    return text.strip().lower()


def _load_rates(path: str) -> dict:
    """region -> tax percent as Decimal (rates.csv stores percents, e.g. 8.25)."""
    rates = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            region = _norm(row["region"])
            if region:
                rates[region] = Decimal(row["tax_pct"].strip())
    return rates


def _load_exempt(path: str) -> frozenset:
    with open(path, newline="", encoding="utf-8") as f:
        return frozenset(
            _norm(row["category"]) for row in csv.DictReader(f) if _norm(row["category"])
        )


_RATES_PCT = _load_rates(_RATES_PATH)
_EXEMPT = _load_exempt(_EXEMPT_PATH)


@dataclass(frozen=True)
class TaxResult:
    """Result of compute_tax. Money fields are dollars rounded to the cent."""

    tax: float                 # tax owed, rounded half up to the cent
    rate: float                # tax rate fraction applied (0.0 for unknown customer)
    discount_rate: float       # discount fraction applied to the taxable amount
    taxable_subtotal: float    # sum of non-exempt line amounts, before discount
    exempt_subtotal: float     # sum of exempt line amounts


def _to_decimal_dollars(value, what: str) -> Decimal:
    if isinstance(value, bool) or not isinstance(value, (int, float, Decimal)):
        raise ValueError(f"{what} must be a number of dollars, got {value!r}")
    # str() avoids binary float noise, e.g. 0.1 -> Decimal("0.1") exactly.
    return Decimal(str(value))


def get_tax_rate(region: Optional[str]) -> float:
    """Tax rate as a fraction for a region (TX -> 0.0825). Raises KeyError if unknown."""
    if region is None:
        raise KeyError("region is None; an unknown customer has no tax rate")
    key = _norm(region)
    if key not in _RATES_PCT:
        raise KeyError(f"no tax rate for region {region!r}")
    return float(_RATES_PCT[key] / _HUNDRED)


def is_exempt(category: str) -> bool:
    """True if items in this category are not taxed."""
    return _norm(category) in _EXEMPT


def compute_tax(
    lines: Iterable[Tuple[str, float]],
    region: Optional[str],
    discount_rate=0,
) -> TaxResult:
    """Compute sales tax for an invoice.

    Rules (data_tax/RULES.md):
      taxable_amount = sum of non-exempt line amounts
      base           = taxable_amount * (1 - discount_rate)
      tax            = base * tax_rate, rounded to the cent (half up)
    An unknown customer (region is None) pays 0% tax.
    """
    taxable = Decimal(0)
    exempt = Decimal(0)
    for category, amount in lines:
        amt = _to_decimal_dollars(amount, "line amount")
        if is_exempt(category):
            exempt += amt
        else:
            taxable += amt

    discount = _to_decimal_dollars(discount_rate, "discount_rate")
    if not (Decimal(0) <= discount <= Decimal(1)):
        raise ValueError(f"discount_rate must be a fraction between 0 and 1, got {discount_rate!r}")

    if region is None:
        rate = Decimal(0)
    else:
        rate = Decimal(str(get_tax_rate(region)))

    base = taxable * (Decimal(1) - discount)
    tax = (base * rate).quantize(_CENT, rounding=ROUND_HALF_UP)

    return TaxResult(
        tax=float(tax),
        rate=float(rate),
        discount_rate=float(discount),
        taxable_subtotal=float(taxable.quantize(_CENT, rounding=ROUND_HALF_UP)),
        exempt_subtotal=float(exempt.quantize(_CENT, rounding=ROUND_HALF_UP)),
    )
