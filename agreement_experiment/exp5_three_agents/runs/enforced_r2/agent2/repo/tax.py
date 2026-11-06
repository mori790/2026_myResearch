"""Sales tax calculation.

Implements the committed decision ``tax_api`` (v1):

    calculate_tax(region, discount_pct, lines) -> (tax_cents, tax_pct)

Rules (data_tax/RULES.md):
  * The tax percent depends on the customer's region (data_tax/rates.csv).
  * Items whose category is listed in data_tax/exempt_categories.csv are not taxed.
  * Taxable base = sum of taxable line amounts, reduced by the customer's
    discount percent:  base = taxable_amount * (100 - discount_pct) / 100
  * tax = base * tax_pct / 100, rounded to the cent (half up).
  * An unknown customer (region None) pays 0% tax.

All money is integer cents. Percentages are decimal.Decimal. The arithmetic is
exact (fractions.Fraction) so that no floating-point error can change the
rounding of the final cent value.
"""

import csv
import os
from decimal import Decimal
from fractions import Fraction
from typing import Iterable, Optional, Sequence, Tuple

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_tax")
_RATES_PATH = os.path.join(_DATA_DIR, "rates.csv")
_EXEMPT_PATH = os.path.join(_DATA_DIR, "exempt_categories.csv")


def _load_rates(path: str) -> dict:
    rates = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            region = row["region"].strip()
            rates[region] = Decimal(row["tax_pct"].strip())
    return rates


def _load_exempt_categories(path: str) -> frozenset:
    with open(path, newline="", encoding="utf-8") as f:
        return frozenset(
            row["category"].strip() for row in csv.DictReader(f) if row["category"].strip()
        )


_RATES = _load_rates(_RATES_PATH)
_EXEMPT_CATEGORIES = _load_exempt_categories(_EXEMPT_PATH)


def tax_rate(region: str) -> Decimal:
    """Return the tax percent for a region (e.g. 'TX' -> Decimal('8.25')).

    Raises KeyError if the region is not listed in rates.csv.
    """
    return _RATES[region]


def is_exempt(category: str) -> bool:
    """True if items in this category are not taxed."""
    return category in _EXEMPT_CATEGORIES


def calculate_tax(
    region: Optional[str],
    discount_pct: int,
    lines: Iterable[Tuple[str, int]],
) -> Tuple[int, Decimal]:
    """Compute sales tax for one order.

    Args:
        region: customer's region code (e.g. 'TX'), or None for an unknown customer.
        discount_pct: customer's discount percent, integer 0..100. It is applied
            only to the taxable lines.
        lines: iterable of (category, line_total_cents) pairs, one per known item.
            Lines whose category is exempt are excluded from the taxable base.

    Returns:
        (tax_cents, tax_pct): tax as integer cents (rounded half up to the cent)
        and the tax percent used as a Decimal (Decimal(0) if no tax applies).

    Raises:
        KeyError: region is not None and not present in rates.csv.
        ValueError: discount_pct outside 0..100, or a negative line amount.
    """
    if not isinstance(discount_pct, int) or isinstance(discount_pct, bool):
        raise ValueError("discount_pct must be an int in 0..100")
    if not 0 <= discount_pct <= 100:
        raise ValueError("discount_pct must be in 0..100")

    # Unknown customer: no tax, no exception (tax_api behaviour).
    if region is None:
        return 0, Decimal(0)

    tax_pct = tax_rate(region)  # KeyError for unknown region

    taxable_cents = 0
    for category, line_total_cents in lines:
        if line_total_cents < 0:
            raise ValueError("line_total_cents must be non-negative")
        if is_exempt(category):
            continue
        taxable_cents += line_total_cents

    # tax = taxable * (100 - discount)/100 * tax_pct/100   (result in cents)
    # Exact rational arithmetic, then round half up to the nearest cent.
    exact_tax_cents = (
        Fraction(taxable_cents)
        * Fraction(100 - discount_pct, 100)
        * Fraction(tax_pct)
        / 100
    )
    tax_cents = int(exact_tax_cents + Fraction(1, 2))  # all values are >= 0
    return tax_cents, tax_pct
