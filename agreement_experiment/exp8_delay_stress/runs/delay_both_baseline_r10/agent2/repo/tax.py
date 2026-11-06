"""Tax module. Owned by agent2. Computes sales tax.

The data files and rules are in data_tax/ next to this file:
  - data_tax/rates.csv              region -> tax_pct
  - data_tax/exempt_categories.csv  categories that are not taxed
  - data_tax/RULES.md               the tax rules

Team conventions:
  - Money amounts are integers in cents (1250 means $12.50).
  - Percentages are percent numbers (10% is 10, 8.25% is 8.25).
  - A lookup that finds nothing raises KeyError.

Public API:
  calculate_tax(lines, customer) -> dict
      lines:    iterable of {"category": str, "amount_cents": int}
                (line totals in cents, quantity already applied)
      customer: None for an unknown customer (0% tax, no discount), or an
                object/dict with `region` (str) and optional `discount_pct`
                (percent number, default 0).
      returns:  {"taxable_cents": int, "discount_pct": number,
                 "tax_pct": number, "tax_cents": int}
                tax_cents is an int rounded half-up to the cent.
"""

import csv
import os
from decimal import Decimal, ROUND_HALF_UP

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_tax")
_RATES_PATH = os.path.join(_DATA_DIR, "rates.csv")
_EXEMPT_PATH = os.path.join(_DATA_DIR, "exempt_categories.csv")

HUNDRED = Decimal(100)


def _load_rates(path=_RATES_PATH):
    """Return {region: Decimal tax_pct}. Decimal avoids float rounding issues."""
    rates = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            region = row["region"].strip()
            rates[region] = Decimal(row["tax_pct"].strip())
    return rates


def _load_exempt_categories(path=_EXEMPT_PATH):
    """Return the set of categories that are not taxed."""
    with open(path, newline="", encoding="utf-8") as f:
        return {row["category"].strip() for row in csv.DictReader(f) if row["category"].strip()}


_RATES = _load_rates()
_EXEMPT_CATEGORIES = _load_exempt_categories()


def get_tax_pct(region):
    """Return the tax percent for a region. Raises KeyError if the region is unknown."""
    return _RATES[region]


def is_exempt(category):
    """True if items of this category are not taxed."""
    return category in _EXEMPT_CATEGORIES


def calculate_tax(lines, customer):
    """Compute sales tax for an order.

    Rules (data_tax/RULES.md):
      taxable_amount = sum of line amounts whose category is not exempt
      base           = taxable_amount * (100 - discount_pct) / 100
      tax            = base * tax_pct / 100, rounded to the cent (half up)
      unknown customer (None) pays 0% tax.
    """
    taxable_cents = 0
    for line in lines:
        amount = line["amount_cents"]
        if not isinstance(amount, int):
            raise TypeError("amount_cents must be an int (cents), got %r" % (amount,))
        if not is_exempt(line["category"]):
            taxable_cents += amount

    if customer is None:
        discount_pct = Decimal(0)
        tax_pct = Decimal(0)
    else:
        if isinstance(customer, dict):
            region = customer["region"]
            raw_discount = customer.get("discount_pct", 0)
        else:
            region = customer.region
            raw_discount = getattr(customer, "discount_pct", 0)

        discount_pct = Decimal(str(raw_discount if raw_discount is not None else 0))
        if not (Decimal(0) <= discount_pct <= HUNDRED):
            raise ValueError("discount_pct must be between 0 and 100, got %s" % discount_pct)
        tax_pct = get_tax_pct(region)  # raises KeyError for an unknown region

    base = Decimal(taxable_cents) * (HUNDRED - discount_pct) / HUNDRED
    tax = base * tax_pct / HUNDRED
    tax_cents = int(tax.quantize(Decimal(1), rounding=ROUND_HALF_UP))

    return {
        "taxable_cents": taxable_cents,
        "discount_pct": float(discount_pct) if discount_pct % 1 else int(discount_pct),
        "tax_pct": float(tax_pct) if tax_pct % 1 else int(tax_pct),
        "tax_cents": tax_cents,
    }
