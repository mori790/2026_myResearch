"""Tax module. Owned by agent2. Computes sales tax. The data files and rules are in data_tax/ next to this file.

Interface (committed decisions tax.api, tax.unknown_customer, tax.rate_pct):
    compute_tax(lines, region, discount) -> float dollars
        lines:    list of (category: str, amount: float dollars), one per order line
        region:   2-letter region code from pricing.get_customer(), or None for an unknown customer (tax 0)
        discount: float fraction from pricing.get_customer() (0.10 = 10%); 0 for an unknown customer
    rate_pct(region) -> str
        nominal sales-tax percent for the region, e.g. "8.25"; "0" when region is None

Internally, money is converted to integer cents and percent arithmetic uses Decimal (no float).
Rounding: the tax is rounded half up to the cent, once, at the end.
Unknown non-None region codes raise KeyError.
"""

import csv
import os
from decimal import Decimal, ROUND_HALF_UP

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_tax")
_CENT = Decimal("100")


def _load_rates():
    rates = {}
    with open(os.path.join(_DATA_DIR, "rates.csv"), newline="") as f:
        for row in csv.DictReader(f):
            region = row["region"].strip().upper()
            rates[region] = row["tax_pct"].strip()
    return rates


def _load_exempt():
    exempt = set()
    with open(os.path.join(_DATA_DIR, "exempt_categories.csv"), newline="") as f:
        for row in csv.DictReader(f):
            exempt.add(row["category"].strip().lower())
    return exempt


_RATES = _load_rates()      # region -> percent string, e.g. "8.25"
_EXEMPT = _load_exempt()    # lower-cased category names that are not taxed


def _to_cents(amount):
    """Convert a dollar amount (float, int, str or Decimal) to integer cents."""
    cents = Decimal(str(amount)) * _CENT
    return int(cents.quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def _region_key(region):
    """Return the rates.csv key for a non-None region. Unknown region -> KeyError."""
    key = str(region).strip().upper()
    if key not in _RATES:
        raise KeyError(f"unknown tax region: {region!r}")
    return key


def rate_pct(region):
    """Nominal sales-tax percent for the region as a decimal string (no % sign)."""
    if region is None:
        return "0"
    return _RATES[_region_key(region)]


def compute_tax(lines, region, discount):
    """Return the sales tax for an order as float dollars, rounded half up to the cent."""
    if region is None:
        # Unknown customer pays 0% tax (RULES.md).
        return 0.0
    tax_pct = Decimal(_RATES[_region_key(region)])

    taxable_cents = 0
    for category, amount in lines:
        if str(category).strip().lower() in _EXEMPT:
            continue
        taxable_cents += _to_cents(amount)

    # base = taxable * (100 - discount_pct) / 100, where discount_pct = discount * 100
    discount_pct = Decimal(str(discount)) * _CENT
    base = Decimal(taxable_cents) * (Decimal(100) - discount_pct) / Decimal(100)

    # tax_cents = base * tax_pct / 100, rounded half up to the cent once, at the end
    tax_cents = int((base * tax_pct / Decimal(100)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    return float(Decimal(tax_cents) / _CENT)
