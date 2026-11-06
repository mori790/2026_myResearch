"""Tax module. Owned by agent2. Computes sales tax.

The data files and rules are in data_tax/ next to this file:
  - rates.csv              region, tax_pct          (tax_pct is a percent number, e.g. 8.25)
  - exempt_categories.csv  category                  (items in these categories are not taxed)
  - RULES.md               the tax rules

Committed team API (tax_api v2, money_unit v3 = float_dollars, percent_unit = fraction):

    compute_tax(region: str | None, lines: list[dict]) -> dict

    lines: one dict per known item, {sku: str, category: str, net_amount: float}
           net_amount = unit_price * qty * (1 - discount_rate), unrounded, in float dollars.
           The customer discount is already applied by the caller, so net_amount is the
           discounted line amount.
    returns: {"rate": float, "tax": float}
           rate = tax fraction (0.0825 for 8.25 percent)
           tax  = tax in dollars, rounded to the cent (ROUND_HALF_UP)

    region None (unknown customer)       -> rate 0.0, tax 0.0
    region not present in rates.csv      -> KeyError (a missing rate is a data error and
                                            must not silently mean "no tax")

Tax rule (RULES.md):
    taxable  = sum of net_amount over lines whose category is NOT exempt
    tax      = taxable * tax_pct / 100, rounded to the cent (half up)
The discount is not applied again here, because net_amount is already discounted.
Rounding happens once, on the final tax amount, so the rounding is not compounded.
"""

import csv
import os
from decimal import ROUND_HALF_UP, Decimal

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_tax")
_CENT = Decimal("0.01")
_HUNDRED = Decimal("100")


def _load_rates(path):
    rates = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            region = row["region"].strip()
            rates[region] = Decimal(row["tax_pct"].strip())  # percent number, e.g. 8.25
    return rates


def _load_exempt(path):
    exempt = set()
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            category = row["category"].strip()
            if category:
                exempt.add(category)
    return exempt


_RATES = _load_rates(os.path.join(_DATA_DIR, "rates.csv"))
_EXEMPT = _load_exempt(os.path.join(_DATA_DIR, "exempt_categories.csv"))


def compute_tax(region, lines):
    """Return {"rate": float fraction, "tax": float dollars rounded to the cent}.

    See the module docstring for the full contract.
    """
    if region is None:
        return {"rate": 0.0, "tax": 0.0}

    tax_pct = _RATES[region]  # KeyError if the region has no rate row

    taxable = Decimal("0")
    for line in lines:
        if line["category"] in _EXEMPT:
            continue
        # str() converts the float to its shortest decimal form first, so 22.5
        # stays exactly 22.5 and the half-up rounding below is exact.
        taxable += Decimal(str(line["net_amount"]))

    tax = (taxable * tax_pct / _HUNDRED).quantize(_CENT, rounding=ROUND_HALF_UP)
    rate = float(tax_pct / _HUNDRED)
    return {"rate": rate, "tax": float(tax)}
