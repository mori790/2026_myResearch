"""Tax module. Owned by agent2. Computes sales tax.

The data files and rules are in data_tax/ next to this file.

Public API (committed decisions tax.api / tax.money / tax.percent / tax.lookup_miss):

    compute_tax(customer, lines) -> float

    customer : dict from pricing.get_customer(), i.e.
               {"id": str, "name": str, "discount": float fraction, "region": str}
               or None for an unknown customer (tax is 0.0).
    lines    : list of {"category": str, "amount": float dollars}, where amount
               is the line total before discount.
    returns  : tax in float dollars, rounded half-up to the cent.

Rules (data_tax/RULES.md):
    * The tax percent depends on the customer's region (rates.csv).
    * Items whose category is listed in exempt_categories.csv are not taxed.
    * base = taxable_amount * (1 - discount)
    * tax  = base * tax_pct / 100, rounded to the cent (half up).
    * An unknown customer pays 0% tax.
    * A region missing from rates.csv raises KeyError.

Money is handled in Decimal internally so that float drift cannot change the
cent rounding.
"""

import csv
import os
from decimal import Decimal, ROUND_HALF_UP

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_tax")
_CENT = Decimal("0.01")


def _load_rates(path):
    """region -> tax percent (Decimal, percent number, e.g. 8.25)."""
    rates = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            rates[row["region"].strip()] = Decimal(row["tax_pct"].strip())
    return rates


def _load_exempt(path):
    """Set of category strings that are not taxed."""
    exempt = set()
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            category = (row.get("category") or "").strip()
            if category:
                exempt.add(category)
    return exempt


_RATES_PCT = _load_rates(os.path.join(_DATA_DIR, "rates.csv"))
_EXEMPT = _load_exempt(os.path.join(_DATA_DIR, "exempt_categories.csv"))


def compute_tax(customer, lines):
    """Return the sales tax for one order, in float dollars rounded half-up to the cent.

    Raises KeyError if the customer's region has no rate in rates.csv.
    """
    if customer is None:
        # Unknown customer pays 0% tax (RULES.md).
        return 0.0

    rate_pct = _RATES_PCT[customer["region"]]  # KeyError on unknown region
    discount = Decimal(str(customer["discount"]))  # fraction, e.g. 0.1 = 10%

    taxable = Decimal("0")
    for line in lines:
        if line["category"] in _EXEMPT:
            continue
        taxable += Decimal(str(line["amount"]))

    base = taxable * (Decimal("1") - discount)
    tax = base * rate_pct / Decimal("100")
    return float(tax.quantize(_CENT, rounding=ROUND_HALF_UP))
