"""Tax module. Owned by agent2. Computes sales tax.

The data files and rules are in data_tax/ next to this file (see data_tax/RULES.md).

API (TAX_API, team convention):
  - Money amounts are integers in cents (1250 == $12.50).
  - Percentages are percent numbers (10 == 10%, 8.25 == 8.25%).
  - A lookup that finds nothing raises KeyError (unknown region).

Boundary with pricing.py (PRICING_API v1, owned by agent1):
  - get_customer() returns discount as a fraction (0.10 == 10%) and region.
    calculate_tax() converts this to a percent number internally.
  - get_item() returns price as float dollars. Callers must convert to cents
    (see dollars_to_cents) before passing amounts to this module.
"""

from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Iterable, Mapping, Optional, Tuple, Union

_DATA_DIR = Path(__file__).resolve().parent / "data_tax"

_HUNDRED = Decimal(100)
_CENT = Decimal(1)


def _load_rates(path: Path) -> dict:
    rates = {}
    with path.open(encoding="utf-8") as f:
        header = f.readline().strip().split(",")
        if header != ["region", "tax_pct"]:
            raise ValueError(f"unexpected header in {path}: {header}")
        for line in f:
            line = line.strip()
            if not line:
                continue
            region, pct = line.split(",")
            rates[region.strip()] = Decimal(pct.strip())
    return rates


def _load_exempt(path: Path) -> frozenset:
    with path.open(encoding="utf-8") as f:
        header = f.readline().strip()
        if header != "category":
            raise ValueError(f"unexpected header in {path}: {header}")
        return frozenset(line.strip() for line in f if line.strip())


_RATES = _load_rates(_DATA_DIR / "rates.csv")          # region -> Decimal percent
_EXEMPT = _load_exempt(_DATA_DIR / "exempt_categories.csv")


def tax_rate_pct(region: str) -> Decimal:
    """Return the sales tax percent for a region (e.g. 'TX' -> Decimal('8.25')).

    Raises KeyError if the region has no rate in rates.csv.
    """
    return _RATES[region]


def is_exempt(category: str) -> bool:
    """True if items in this category are not taxed (exempt_categories.csv)."""
    return category in _EXEMPT


def dollars_to_cents(amount: Union[int, float, str, Decimal]) -> int:
    """Convert a dollar amount (e.g. pricing.py's float price) to integer cents, half up."""
    return int((Decimal(str(amount)) * _HUNDRED).quantize(_CENT, rounding=ROUND_HALF_UP))


def taxable_amount_cents(lines: Iterable[Tuple[str, int]]) -> int:
    """Sum of the line amounts (in cents) whose category is not exempt.

    lines: iterable of (category, amount_cents) pairs.
    """
    total = 0
    for category, amount_cents in lines:
        _check_cents(amount_cents)
        if not is_exempt(category):
            total += amount_cents
    return total


def calculate_tax(
    lines: Iterable[Tuple[str, int]],
    customer: Optional[Mapping],
) -> int:
    """Return the sales tax for an order, in integer cents.

    lines:    iterable of (category, amount_cents) pairs, one per line item.
    customer: the dict returned by pricing.get_customer() (keys: 'region',
              'discount' as a fraction, e.g. 0.10 == 10%), or None if the
              customer is unknown. An unknown customer pays 0 tax.

    Rules (data_tax/RULES.md):
      taxable  = sum of non-exempt line amounts (cents)
      base     = taxable * (100 - discount_pct) / 100
      tax      = base * tax_pct / 100, rounded to the cent (half up)
    """
    if customer is None:
        # Still validate the lines so bad input is not silently accepted.
        taxable_amount_cents(lines)
        return 0

    region = customer["region"]
    discount_pct = Decimal(str(customer["discount"])) * _HUNDRED
    if not (Decimal(0) <= discount_pct <= _HUNDRED):
        raise ValueError(f"discount out of range: {customer['discount']!r}")

    taxable = taxable_amount_cents(lines)
    rate_pct = tax_rate_pct(region)  # KeyError for unknown region

    base = Decimal(taxable) * (_HUNDRED - discount_pct) / _HUNDRED
    tax = base * rate_pct / _HUNDRED
    return int(tax.quantize(_CENT, rounding=ROUND_HALF_UP))


def _check_cents(value) -> None:
    if not isinstance(value, int) or isinstance(value, bool):
        raise TypeError(f"amount must be an integer number of cents, got {value!r}")
    if value < 0:
        raise ValueError(f"amount must be non-negative, got {value!r}")
