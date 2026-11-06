"""Tax module. Owned by agent2. Computes sales tax.

Implements the committed decisions `money_units` v1 and `tax_api` v2:

    compute_tax(lines, region, discount_pct) -> dict

* All money amounts are integer cents (int). Percents are Decimal.
* `lines` are GROSS line totals (quantity * unit price, before discount and tax).
  Callers must not pre-discount them; the discount is applied once, here.
* The data files live in data_tax/ next to this module (rates.csv,
  exempt_categories.csv). RULES.md in that folder is the source of the rules.

Rules (from data_tax/RULES.md):
  taxable     = sum of amount_cents of lines whose category is NOT exempt
  base        = taxable * (100 - discount_pct) / 100        (discount on taxable only)
  tax         = base * tax_pct / 100, rounded to the cent (half up)
  unknown region (or None) -> tax_pct 0
"""

import csv
import os
from decimal import Decimal, ROUND_HALF_UP

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_tax")
_RATES_PATH = os.path.join(_DATA_DIR, "rates.csv")
_EXEMPT_PATH = os.path.join(_DATA_DIR, "exempt_categories.csv")

_HUNDRED = Decimal(100)
_CENT = Decimal(1)


def _load_rates(path=_RATES_PATH):
    """Return {region_code: Decimal tax_pct} from rates.csv."""
    rates = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            region = row["region"].strip().upper()
            rates[region] = Decimal(row["tax_pct"].strip())
    return rates


def _load_exempt(path=_EXEMPT_PATH):
    """Return the set of exempt category names from exempt_categories.csv."""
    exempt = set()
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            name = row["category"].strip().lower()
            if name:
                exempt.add(name)
    return exempt


_RATES = _load_rates()
_EXEMPT = _load_exempt()


def _round_half_up(value):
    """Round an exact Decimal to a whole number of cents, half up. Returns int."""
    return int(value.quantize(_CENT, rounding=ROUND_HALF_UP))


def _normalize_discount(discount_pct):
    """None -> 0. Accept Decimal or int in 0..100. Anything else is an error."""
    if discount_pct is None:
        return Decimal(0)
    if isinstance(discount_pct, bool) or not isinstance(discount_pct, (int, Decimal)):
        raise ValueError(f"discount_pct must be Decimal, int or None, got {discount_pct!r}")
    value = Decimal(discount_pct)
    if not (Decimal(0) <= value <= _HUNDRED):
        raise ValueError(f"discount_pct must be in 0..100, got {discount_pct!r}")
    return value


def _normalize_amount(amount_cents):
    """amount_cents must be a non-negative int (bool is rejected)."""
    if isinstance(amount_cents, bool) or not isinstance(amount_cents, int):
        raise ValueError(f"amount_cents must be int, got {amount_cents!r}")
    if amount_cents < 0:
        raise ValueError(f"amount_cents must be >= 0, got {amount_cents!r}")
    return amount_cents


def compute_tax(lines, region, discount_pct):
    """Compute sales tax for one order.

    Args:
        lines: iterable of {"category": str, "amount_cents": int}, gross line totals.
        region: customer region code (e.g. "TX", "NY", "OR"), or None.
            Unknown or None region means tax_pct 0.
        discount_pct: customer discount percent (Decimal or int, 0..100), or None (= 0).

    Returns:
        {
          "taxable_cents": int,   # non-exempt line total, before discount
          "discount_cents": int,  # taxable_cents * discount_pct / 100, rounded (for display)
          "tax_pct": Decimal,     # rate from rates.csv; 0 if unknown region
          "tax_cents": int,       # rounded once, from the exact discounted base
        }

    Raises:
        ValueError: negative or non-int amount_cents, discount_pct outside 0..100,
            or a wrong type for discount_pct.
    """
    discount = _normalize_discount(discount_pct)

    taxable_cents = 0
    for line in lines:
        amount = _normalize_amount(line["amount_cents"])
        category = str(line["category"]).strip().lower()
        if category not in _EXEMPT:
            taxable_cents += amount

    if region is None:
        tax_pct = Decimal(0)
    else:
        tax_pct = _RATES.get(str(region).strip().upper(), Decimal(0))

    discount_cents = _round_half_up(Decimal(taxable_cents) * discount / _HUNDRED)
    # base = taxable * (100 - d) / 100 (cents); tax = base * rate / 100 (cents).
    # Exact Decimal arithmetic, one rounding at the end.
    tax_cents = _round_half_up(
        Decimal(taxable_cents) * (_HUNDRED - discount) * tax_pct / (_HUNDRED * _HUNDRED)
    )

    return {
        "taxable_cents": taxable_cents,
        "discount_cents": discount_cents,
        "tax_pct": tax_pct,
        "tax_cents": tax_cents,
    }
