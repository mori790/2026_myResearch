"""Tax module. Owned by agent2. Computes sales tax.

The data files and rules are in data_tax/ next to this file (see data_tax/RULES.md).

Agreed units (committed decisions units_repr and tax_api):
- Money is an integer number of cents (1250 means $12.50).
- Percentages are percent numbers (10 means 10%, 8.25 means 8.25%).
- A lookup that finds nothing raises KeyError (tax_rate), except that compute_tax
  treats an unknown or missing region as 0% tax, as RULES.md requires.
"""

import csv
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

_DATA_DIR = Path(__file__).resolve().parent / "data_tax"


def _load_rates(path):
    """Return {region_code: tax_pct as Decimal} from rates.csv."""
    rates = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            region = row["region"].strip()
            rates[region] = Decimal(row["tax_pct"].strip())
    return rates


def _load_exempt(path):
    """Return the set of exempt category names from exempt_categories.csv."""
    exempt = set()
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            category = row["category"].strip()
            if category:
                exempt.add(category)
    return exempt


_RATES = _load_rates(_DATA_DIR / "rates.csv")          # region -> tax percent
_EXEMPT = _load_exempt(_DATA_DIR / "exempt_categories.csv")  # exempt categories


def tax_rate(region):
    """Return the tax percent for `region` (e.g. 8.25 for TX).

    Raises KeyError if the region is not listed in rates.csv.
    """
    if region is None:
        raise KeyError(region)
    return float(_RATES[region])


def compute_tax(region, discount_pct, lines):
    """Return the sales tax for an order, in integer cents (>= 0).

    region:       customer region code (e.g. "TX"), or None if the customer is unknown.
                  An unknown or None region pays 0% tax (no exception).
    discount_pct: customer discount as a percent number (10 means 10% off), 0 if none.
                  The discount applies only to taxable lines.
    lines:        list of dicts {"category": str, "amount_cents": int} for all invoice
                  lines; amount_cents is the line total before discount. Lines whose
                  category is exempt (data_tax/exempt_categories.csv) are not taxed.

    Rule (RULES.md):
        taxable   = sum of amount_cents of non-exempt lines
        base      = taxable * (100 - discount_pct) / 100
        tax       = base * tax_pct / 100, rounded half up to the cent
    Only the final tax is rounded; exact Decimal arithmetic is used throughout.
    """
    rate = _RATES.get(region)
    if rate is None:
        return 0

    taxable = sum(
        int(line["amount_cents"])
        for line in lines
        if line["category"] not in _EXEMPT
    )
    discount = Decimal(str(discount_pct))

    # tax_cents = taxable * (100 - discount) / 100 * rate / 100
    tax = Decimal(taxable) * (Decimal(100) - discount) * rate / Decimal(10000)
    tax_cents = int(tax.quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    return max(tax_cents, 0)
