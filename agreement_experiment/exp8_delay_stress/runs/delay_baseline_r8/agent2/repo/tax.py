"""Tax module. Owned by agent2. Computes sales tax. The data files and rules are in data_tax/ next to this file.

Team conventions (followed everywhere in this module):
  - Money amounts are integers in cents (1250 means $12.50).
  - Percentages are percent numbers (10% is 10, 8.25% is 8.25).
  - A lookup that finds nothing raises KeyError.

Public API:
  compute_tax(lines, region, discount_pct) -> int   (tax in cents)
  tax_pct(region) -> float                           (sales tax percent for a region)

Rules (data_tax/RULES.md):
  - Tax percent depends on the customer's region (data_tax/rates.csv).
  - Lines whose category is listed in data_tax/exempt_categories.csv are not taxed.
  - base = taxable_amount * (100 - discount_pct) / 100
  - tax  = base * tax_pct / 100, rounded to the cent (half up).
  - An unknown customer (region None) pays 0% tax.
"""

import csv
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

_DATA_DIR = Path(__file__).resolve().parent / "data_tax"


def _normalize_category(category):
    return str(category).strip().lower()


def _load_rates(path):
    rates = {}
    with path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            region = row["region"].strip()
            rates[region] = Decimal(row["tax_pct"].strip())
    return rates


def _load_exempt(path):
    exempt = set()
    with path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            category = _normalize_category(row["category"])
            if category:
                exempt.add(category)
    return frozenset(exempt)


_RATES = _load_rates(_DATA_DIR / "rates.csv")          # region -> Decimal percent
_EXEMPT = _load_exempt(_DATA_DIR / "exempt_categories.csv")  # normalized categories


def tax_pct(region):
    """Return the sales tax percent (e.g. 8.25) for a region code such as 'TX'.

    region=None means an unknown customer, who pays 0%.
    Raises KeyError if a non-None region is not in rates.csv.
    """
    if region is None:
        return 0.0
    return float(_RATES[str(region).strip()])


def compute_tax(lines, region, discount_pct):
    """Compute sales tax for one order, in integer cents.

    lines        : iterable of objects/dicts with a category and an amount in cents.
                   Accepts dicts {"category": str, "amount_cents": int} or
                   objects with attributes `category` and `amount_cents`.
                   amount_cents is the line total (quantity * unit price).
    region       : customer region code (e.g. 'TX'), or None for an unknown customer.
    discount_pct : customer discount as a percent number (10 means 10%).

    Returns the tax amount as an int number of cents, rounded half up once at the end.
    Raises KeyError for an unknown non-None region, ValueError for a discount outside 0..100,
    TypeError for a non-integer amount.
    """
    if region is None:
        return 0

    rate = _RATES[str(region).strip()]  # KeyError if the region is unknown

    discount = Decimal(str(discount_pct))
    if not (Decimal(0) <= discount <= Decimal(100)):
        raise ValueError(f"discount_pct must be between 0 and 100, got {discount_pct!r}")

    taxable_cents = 0
    for line in lines:
        if isinstance(line, dict):
            category, amount = line["category"], line["amount_cents"]
        else:
            category, amount = line.category, line.amount_cents
        if isinstance(amount, bool) or not isinstance(amount, int):
            raise TypeError(f"amount_cents must be an int (cents), got {amount!r}")
        if _normalize_category(category) in _EXEMPT:
            continue
        taxable_cents += amount

    # tax = taxable * (100 - discount)/100 * rate/100 ; keep exact with Decimal, round once.
    raw = Decimal(taxable_cents) * (Decimal(100) - discount) * rate / Decimal(10000)
    return int(raw.quantize(Decimal("1"), rounding=ROUND_HALF_UP))
