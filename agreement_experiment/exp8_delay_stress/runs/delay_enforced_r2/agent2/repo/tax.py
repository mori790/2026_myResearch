"""Tax module. Owned by agent2. Computes sales tax.

The data files and rules are in data_tax/ next to this file.

Interface (committed decision TAX_API v2):
    get_sales_tax(region, lines, discount) -> {"rate": float, "tax": float} or None

  region    : customer.region string such as 'TX', or None for an unknown customer
              (0 tax). An unknown region string returns None (invoice treats as 0 tax).
  lines     : list of {"category": str, "amount": float dollars before discount}
              for each known line item.
  discount  : float fraction from customer.discount (0.10 = 10%). It is applied only
              to the taxable base (exempt lines are not discounted).
  returns   : {"rate": float fraction (e.g. 0.0825), "tax": float dollars rounded
              half-up to 2 dp}. For region None: {"rate": 0.0, "tax": 0.0}.

Internal arithmetic (team standard): amounts are converted to integer cents and
the tax math is exact (Decimal), rounded half-up to the cent.

Rules (data_tax/RULES.md):
  base = taxable_amount * (100 - discount_pct) / 100
  tax  = base * tax_pct / 100, rounded to the cent (half up)
"""

import csv
import os
from decimal import Decimal, ROUND_HALF_UP

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_tax")
_HUNDRED = Decimal(100)
_ONE = Decimal(1)


def _load_rates():
    """Return {region: Decimal tax percent} from rates.csv."""
    rates = {}
    path = os.path.join(_DATA_DIR, "rates.csv")
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            region = row["region"].strip()
            if region:
                rates[region] = Decimal(row["tax_pct"].strip())
    return rates


def _load_exempt_categories():
    """Return the set of exempt category names from exempt_categories.csv."""
    path = os.path.join(_DATA_DIR, "exempt_categories.csv")
    with open(path, newline="", encoding="utf-8") as f:
        return {row["category"].strip() for row in csv.DictReader(f)
                if row["category"].strip()}


_RATES = _load_rates()           # region -> tax percent (Decimal), e.g. 8.25
_EXEMPT = _load_exempt_categories()


def _to_cents(dollars):
    """Convert a float-dollar amount to integer cents (half up)."""
    return int((Decimal(str(dollars)) * _HUNDRED).quantize(_ONE, rounding=ROUND_HALF_UP))


def get_sales_tax(region, lines, discount):
    """Compute sales tax per TAX_API v2. See the module docstring for the contract."""
    d = Decimal(str(discount))
    if d < 0 or d > 1:
        raise ValueError("discount must be a fraction between 0 and 1, got %r" % (discount,))

    if region is None:  # unknown customer pays no tax
        return {"rate": 0.0, "tax": 0.0}

    tax_pct = _RATES.get(region)
    if tax_pct is None:  # unknown region string -> None (committed TAX_API v2)
        return None

    taxable_cents = 0
    for line in lines:
        if line["category"].strip() in _EXEMPT:
            continue
        taxable_cents += _to_cents(line["amount"])

    # base in cents after the discount; all exact Decimal arithmetic
    base_cents = Decimal(taxable_cents) * (1 - d)
    tax_cents = (base_cents * tax_pct / _HUNDRED).quantize(_ONE, rounding=ROUND_HALF_UP)

    return {
        "rate": float(tax_pct / _HUNDRED),
        "tax": float(tax_cents / _HUNDRED),
    }
