"""Tax module. Owned by agent2. Computes sales tax.

The data files and rules are in data_tax/ next to this file:
  - rates.csv                : region -> tax percent (e.g. TX -> 8.25)
  - exempt_categories.csv    : item categories that are not taxed
  - RULES.md                 : the tax rules

Team conventions (see agreement topic "tax_api"):
  - Money amounts are integers in cents (1250 means $12.50).
  - Percentages are percent numbers (10% is 10, 8.25% is 8.25).
  - A lookup that finds nothing raises KeyError.

Rules implemented (from RULES.md):
  - The tax percent depends on the customer's region (rates.csv).
  - Items whose category is listed in exempt_categories.csv are not taxed.
  - base = taxable_amount * (100 - discount_pct) / 100
  - tax  = base * tax_pct / 100, rounded to the cent (half up).
  - An unknown customer (region None) pays 0% tax.
"""

import csv
import os
from decimal import Decimal, ROUND_HALF_UP

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_tax")
_RATES_PATH = os.path.join(_DATA_DIR, "rates.csv")
_EXEMPT_PATH = os.path.join(_DATA_DIR, "exempt_categories.csv")

_rates = None
_exempt = None


def _load_rates():
    """Return {region: Decimal(tax_pct)} read from rates.csv (loaded once)."""
    global _rates
    if _rates is None:
        rates = {}
        with open(_RATES_PATH, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                region = row["region"].strip()
                # Keep the exact decimal text from the file, e.g. "8.875".
                rates[region] = Decimal(row["tax_pct"].strip())
        _rates = rates
    return _rates


def _load_exempt():
    """Return the set of exempt item categories read from exempt_categories.csv."""
    global _exempt
    if _exempt is None:
        exempt = set()
        with open(_EXEMPT_PATH, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                category = (row.get("category") or "").strip()
                if category:
                    exempt.add(category)
        _exempt = exempt
    return _exempt


def tax_rate_pct(region):
    """Return the sales tax percent for a customer region, as a Decimal.

    region: region code string such as "TX", or None for an unknown customer.
    None -> Decimal("0") (unknown customers pay no tax).
    A region code that is not in rates.csv -> KeyError.
    """
    if region is None:
        return Decimal("0")
    return _load_rates()[region]


def is_exempt(category):
    """Return True if items in this category are not taxed."""
    return category in _load_exempt()


def compute_tax(lines, region, discount_pct=0):
    """Compute sales tax for an invoice, in integer cents.

    lines:        iterable of (amount_cents: int, category: str), one per
                  invoice line. Lines in exempt categories are not taxed.
    region:       customer region code (e.g. "TX"), or None for an unknown
                  customer (0% tax). An unrecognized region -> KeyError.
    discount_pct: customer discount as a percent number (10 means 10%).
                  Defaults to 0.

    Returns the tax amount as an int number of cents, rounded half up
    once, at the end of the calculation.
    """
    taxable_cents = 0
    for amount_cents, category in lines:
        if isinstance(amount_cents, bool) or not isinstance(amount_cents, int):
            raise TypeError(
                "amount_cents must be an int number of cents, got %r"
                % (amount_cents,)
            )
        if not is_exempt(category):
            taxable_cents += amount_cents

    rate = tax_rate_pct(region)
    discount = Decimal(str(discount_pct))

    # Exact decimal arithmetic; no floats, so no binary rounding error.
    base = Decimal(taxable_cents) * (Decimal(100) - discount) / Decimal(100)
    tax = base * rate / Decimal(100)
    return int(tax.quantize(Decimal("1"), rounding=ROUND_HALF_UP))
