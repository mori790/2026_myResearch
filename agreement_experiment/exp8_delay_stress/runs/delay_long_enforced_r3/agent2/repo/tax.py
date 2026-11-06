"""Tax module. Owned by agent2. Computes sales tax.

The data files and rules are in data_tax/ next to this file.

Committed API (agree.py topic 'tax_api' v2):
    compute_tax(taxable_lines, region, discount_pct) -> int   (cents)
    rate_percent(region) -> float                              (e.g. 8.25)

Conventions (team standard, as committed):
    - money amounts are integer cents (1250 == $12.50)
    - percentages are percent numbers (10 == 10%)
    - unknown region (None) means an unknown customer: tax is 0, no error
    - a non-None region missing from rates.csv raises KeyError

Important for callers: `taxable_lines` must contain the GROSS line amounts
(before the customer's discount). The discount is applied here, once, via
`discount_pct`. Passing already-discounted amounts would discount twice.
"""

import csv
import os
from decimal import Decimal, ROUND_HALF_UP

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_tax")
_RATES_PATH = os.path.join(_DATA_DIR, "rates.csv")
_EXEMPT_PATH = os.path.join(_DATA_DIR, "exempt_categories.csv")


def _load_rates(path):
    """Return {region: Decimal percent} from rates.csv (columns: region,tax_pct)."""
    rates = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            region = row["region"].strip()
            rates[region] = Decimal(row["tax_pct"].strip())
    return rates


def _load_exempt(path):
    """Return the set of exempt category names (column: category)."""
    with open(path, newline="", encoding="utf-8") as f:
        return {row["category"].strip() for row in csv.DictReader(f) if row["category"].strip()}


_RATES = _load_rates(_RATES_PATH)
_EXEMPT = _load_exempt(_EXEMPT_PATH)


def _check_cents(value, name):
    # bool is a subclass of int in Python; reject it explicitly.
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be an integer number of cents, got {value!r}")


def _check_percent(value, name):
    if isinstance(value, bool) or not isinstance(value, (int, float, Decimal)):
        raise TypeError(f"{name} must be a percent number, got {value!r}")
    if not (0 <= value <= 100):
        raise ValueError(f"{name} must be between 0 and 100, got {value!r}")


def _rate_for(region):
    """Return the Decimal tax percent for a region. None -> 0 (unknown customer)."""
    if region is None:
        return Decimal(0)
    if region not in _RATES:
        raise KeyError(f"unknown tax region: {region!r}")
    return _RATES[region]


def rate_percent(region):
    """Tax percent for a customer region, e.g. 8.25. None (unknown customer) -> 0."""
    return float(_rate_for(region))


def compute_tax(taxable_lines, region, discount_pct):
    """Return the sales tax for an order, in integer cents, rounded half up.

    taxable_lines: iterable of (line_amount_cents: int, category: str), gross amounts.
                   Lines whose category is in exempt_categories.csv are not taxed.
    region:        customer region code (e.g. 'TX'), or None for an unknown customer.
    discount_pct:  customer discount in percent numbers (10 == 10% off).

    base = taxable_sum * (100 - discount_pct) / 100
    tax  = base * rate_pct / 100, rounded half up to the cent.
    """
    _check_percent(discount_pct, "discount_pct")
    rate = _rate_for(region)

    taxable_sum = 0
    for line_amount, category in taxable_lines:
        _check_cents(line_amount, "line_amount")
        if line_amount < 0:
            raise ValueError(f"line amount must not be negative, got {line_amount}")
        if category in _EXEMPT:
            continue
        taxable_sum += line_amount

    if region is None or rate == 0 or taxable_sum == 0:
        return 0

    # Exact decimal arithmetic avoids binary float errors at half-cent boundaries.
    base = Decimal(taxable_sum) * (Decimal(100) - Decimal(str(discount_pct))) / Decimal(100)
    tax = base * rate / Decimal(100)
    return int(tax.quantize(Decimal(1), rounding=ROUND_HALF_UP))
