"""Tax module. Owned by agent2. Computes sales tax. The data files and rules are in data_tax/ next to this file.

Committed interface (tax_api v2):
    compute_tax(region, lines, discount=0) -> Decimal   (dollars, quantized to 0.01, ROUND_HALF_UP)

    region    customer region (e.g. "TX") from pricing; None = unknown customer -> 0 tax.
              A non-None region that is not in rates.csv raises KeyError.
    lines     iterable of (category, amount) pairs, one per line item, BEFORE discount.
              amount is dollars (float or Decimal). Exempt categories are not taxed.
    discount  fraction OFF (0.10 = 10% off). Applied to the taxable sum only.
              Pass the raw discount, not a pre-discounted subtotal.

Rules (data_tax/RULES.md):
    taxable = sum of line amounts whose category is not exempt
    base    = taxable * (1 - discount)
    tax     = base * tax_pct / 100, rounded to the cent (half up)

Internally the arithmetic is done in integer cents (Decimal, exact) and converted to dollars at the end.

Additional helper (not part of the committed API, added for accuracy):
    tax_percent(region) -> Decimal   tax percent for a region (e.g. Decimal('8.25')); None -> Decimal('0');
                                     unknown region raises KeyError.
"""

import csv
import os
from decimal import Decimal, ROUND_HALF_UP

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_tax")
_RATES_PATH = os.path.join(_DATA_DIR, "rates.csv")
_EXEMPT_PATH = os.path.join(_DATA_DIR, "exempt_categories.csv")

_CENT = Decimal("0.01")
_HUNDRED = Decimal(100)


def _load_rates(path=_RATES_PATH):
    """Return {region: Decimal tax percent} from rates.csv."""
    rates = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            region = row["region"].strip()
            rates[region] = Decimal(row["tax_pct"].strip())
    return rates


def _load_exempt(path=_EXEMPT_PATH):
    """Return the set of exempt category names (normalized) from exempt_categories.csv."""
    exempt = set()
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            name = (row.get("category") or "").strip().lower()
            if name:
                exempt.add(name)
    return exempt


_RATES = _load_rates()
_EXEMPT = _load_exempt()


def is_exempt(category):
    """True if items of this category are not taxed."""
    return str(category).strip().lower() in _EXEMPT


def tax_percent(region):
    """Tax percent for a region as a Decimal (e.g. Decimal('8.25')).

    None (unknown customer) -> Decimal('0'). Unknown region -> KeyError.
    """
    if region is None:
        return Decimal(0)
    if region not in _RATES:
        raise KeyError(f"unknown tax region: {region!r}")
    return _RATES[region]


def _to_decimal(value, name):
    if isinstance(value, bool) or not isinstance(value, (int, float, Decimal)):
        raise TypeError(f"{name} must be a number, got {value!r}")
    return Decimal(str(value))


def compute_tax(region, lines, discount=0):
    """Compute sales tax for one order. Returns Decimal dollars rounded to the cent (half up)."""
    discount_frac = _to_decimal(discount, "discount")
    if discount_frac < 0 or discount_frac > 1:
        raise ValueError(f"discount must be a fraction between 0 and 1 (0.10 = 10%), got {discount!r}")

    # 1. Taxable amount in cents: sum of non-exempt line amounts.
    taxable_cents = Decimal(0)
    for category, amount in lines:
        cents = _to_decimal(amount, "line amount") * _HUNDRED
        if not is_exempt(category):
            taxable_cents += cents

    # 2. Discount applies to the taxable sum only: base = taxable * (1 - discount).
    base_cents = taxable_cents * (Decimal(1) - discount_frac)

    # 3. tax = base * tax_pct / 100, rounded to the cent (half up).
    tax_cents = (base_cents * tax_percent(region) / _HUNDRED).quantize(Decimal("1"), rounding=ROUND_HALF_UP)

    return (tax_cents / _HUNDRED).quantize(_CENT, rounding=ROUND_HALF_UP)
