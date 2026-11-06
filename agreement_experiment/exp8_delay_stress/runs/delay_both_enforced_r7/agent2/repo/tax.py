"""Sales tax calculation (owned by agent2).

Agreed interface (shared decision log, topic ``tax_interface`` v3 and
``tax_unknown_customer`` v1):

    compute_tax(region, lines, discount) -> float
        region   : customer region code (e.g. "TX") from pricing.get_customer,
                   or None for an unknown customer (tax is 0.0).
        lines    : list of (line_amount, category) for every known line item,
                   line_amount in float dollars, BEFORE discount and tax.
                   Categories listed in data_tax/exempt_categories.csv are not taxed.
        discount : customer discount as a fraction (0.10 means 10% off), applied
                   to the taxable amount only.
        returns  : total tax in float dollars, rounded to the cent (half up).

    tax_rate(region) -> float
        Tax rate as a fraction (0.0825 for TX). None -> 0.0.
        An unknown region code raises KeyError.

Rules (data_tax/RULES.md):
    taxable  = sum of line amounts whose category is not exempt
    base     = taxable * (1 - discount)
    tax      = base * tax_pct / 100, rounded to the cent (half up)

Internally, floats are converted with Decimal(str(x)) and all arithmetic is
done in exact Decimal, so the cent rounding is not affected by float error.
"""

import csv
import os
from decimal import Decimal, ROUND_HALF_UP

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_tax")
_RATES_PATH = os.path.join(_DATA_DIR, "rates.csv")
_EXEMPT_PATH = os.path.join(_DATA_DIR, "exempt_categories.csv")

_CENT = Decimal("0.01")
_HUNDRED = Decimal("100")


def _load_rates(path):
    """Return {region: Decimal tax percent} loaded from rates.csv."""
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


_RATES = _load_rates(_RATES_PATH)            # {region: percent as Decimal}
_EXEMPT = _load_exempt(_EXEMPT_PATH)         # {category, ...}


def _rate_pct(region):
    """Tax percent (Decimal) for a non-None region. Unknown region -> KeyError."""
    if region not in _RATES:
        raise KeyError(f"unknown tax region: {region!r}")
    return _RATES[region]


def tax_rate(region):
    """Tax rate as a fraction (e.g. 0.0825). None region -> 0.0."""
    if region is None:
        return 0.0
    return float(_rate_pct(region) / _HUNDRED)


def compute_tax(region, lines, discount):
    """Total sales tax in float dollars, rounded to the cent (half up).

    See the module docstring for the agreed interface and rules.
    """
    if region is None:  # unknown customer pays no tax
        return 0.0

    pct = _rate_pct(region)  # raises KeyError for an unknown region

    taxable = Decimal("0")
    for line_amount, category in lines:
        if category in _EXEMPT:
            continue
        taxable += Decimal(str(line_amount))

    discount_frac = Decimal(str(discount))
    base = taxable * (Decimal("1") - discount_frac)
    tax = base * pct / _HUNDRED
    tax = tax.quantize(_CENT, rounding=ROUND_HALF_UP)
    return float(tax)
