"""Tax module. Owned by agent2. Computes sales tax.

The data files and rules are in data_tax/ next to this file (see data_tax/RULES.md).

Committed team API (decision log: TAX_API, TAX_UNKNOWN_REGION):

    get_tax_rate(region) -> float or None
        Tax rate as a fraction (8.25% -> 0.0825). None if the region is not in rates.csv.

    compute_tax(customer, lines) -> float
        customer: dict from pricing.get_customer() (keys: discount as a fraction, region),
                  or None for an unknown customer (tax is 0.0).
        lines:    list of dicts with keys
                  category (str)  - matched case-insensitively against exempt_categories.csv
                  amount   (float dollars) - line total = quantity * unit_price, before discount
        Returns the tax in float dollars, rounded half-up to the cent.

Units follow the committed MONEY_UNIT (float dollars) and PERCENT_UNIT (fraction).
Internally all arithmetic uses Decimal so that rounding is exact and not affected
by binary floating-point error. Rounding happens once, on the final tax amount.

Rules (data_tax/RULES.md):
    taxable   = sum of amounts of lines whose category is not exempt
    base      = taxable * (1 - discount)            # discount is a fraction
    tax       = round_half_up(base * rate, cents)   # rate is a fraction
"""

import csv
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

_DATA_DIR = Path(__file__).resolve().parent / "data_tax"
_CENT = Decimal("0.01")


def _load_rates():
    """Return {REGION: Decimal fraction}, e.g. {'TX': Decimal('0.0825')}."""
    rates = {}
    with open(_DATA_DIR / "rates.csv", newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            region = row["region"].strip().upper()
            if not region:
                continue
            # rates.csv stores percent numbers (8.25); convert to fraction (0.0825).
            rates[region] = Decimal(row["tax_pct"].strip()) / Decimal(100)
    return rates


def _load_exempt_categories():
    """Return the set of exempt categories, normalized to lowercase and stripped."""
    exempt = set()
    with open(_DATA_DIR / "exempt_categories.csv", newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            category = (row.get("category") or "").strip().lower()
            if category:
                exempt.add(category)
    return exempt


_RATES = _load_rates()
_EXEMPT = _load_exempt_categories()


def get_tax_rate(region):
    """Return the tax rate for a region as a fraction, or None if the region is unknown."""
    rate = _RATES.get(str(region).strip().upper())
    return None if rate is None else float(rate)


def _is_exempt(category):
    return str(category).strip().lower() in _EXEMPT


def compute_tax(customer, lines):
    """Return the sales tax for an order as float dollars, rounded half-up to the cent.

    Raises KeyError if the customer is known but its region has no row in rates.csv
    (TAX_UNKNOWN_REGION): a missing rate must not silently become 0% tax.
    """
    if customer is None:
        # Unknown customer pays 0% tax (RULES.md).
        return 0.0

    region = str(customer["region"]).strip().upper()
    if region not in _RATES:
        raise KeyError(f"no tax rate for region {customer['region']!r}")
    rate = _RATES[region]

    taxable = Decimal(0)
    for line in lines:
        if not _is_exempt(line["category"]):
            taxable += Decimal(str(line["amount"]))

    discount = Decimal(str(customer["discount"]))  # fraction, e.g. 0.10 = 10%
    base = taxable * (Decimal(1) - discount)
    tax = (base * rate).quantize(_CENT, rounding=ROUND_HALF_UP)
    return float(tax)
