"""Tax module. Owned by agent2. Computes sales tax. The data files and rules are in data_tax/ next to this file.

Committed interface (decision tax_interface v6):

    compute_tax(region, taxable_lines, discount_pct) -> Decimal
    rate_pct(region) -> Decimal

Units (committed decisions):
    money_unit   = decimal_dollars   -> amounts are decimal.Decimal dollars, quantized to 0.01 (ROUND_HALF_UP)
    percent_unit = percent_number    -> 10 means 10%, 8.25 means 8.25%
    not_found    = return_none_caller_checks (pricing only). Tax keeps its own rules:
                   region None  -> unknown customer, tax 0.00
                   unknown region string -> KeyError
"""

import csv
import os
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_tax")
_RATES_PATH = os.path.join(_DATA_DIR, "rates.csv")
_EXEMPT_PATH = os.path.join(_DATA_DIR, "exempt_categories.csv")

_CENT = Decimal("0.01")
_HUNDRED = Decimal("100")
_ZERO_CENTS = Decimal("0.00")


def _to_decimal(value, name):
    """Convert an input to Decimal. Floats are rejected so rounding stays exact."""
    if isinstance(value, bool):
        raise TypeError(f"{name} must be a Decimal, int or str, not bool")
    if isinstance(value, float):
        raise TypeError(f"{name} must not be a float; use Decimal (decimal_dollars / percent_number)")
    if isinstance(value, Decimal):
        return value
    if isinstance(value, (int, str)):
        try:
            return Decimal(str(value))
        except InvalidOperation as exc:
            raise ValueError(f"{name} is not a valid number: {value!r}") from exc
    raise TypeError(f"{name} must be a Decimal, int or str, not {type(value).__name__}")


def _load_rates(path):
    """Map region string -> tax percent (Decimal, percent_number)."""
    rates = {}
    with open(path, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            region = row["region"].strip()
            rates[region] = Decimal(row["tax_pct"].strip())
    return rates


def _load_exempt(path):
    """Set of exempt category names (normalized: stripped, lower case)."""
    exempt = set()
    with open(path, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            category = row["category"].strip().lower()
            if category:
                exempt.add(category)
    return exempt


_RATES = _load_rates(_RATES_PATH)
_EXEMPT = _load_exempt(_EXEMPT_PATH)


def rate_pct(region):
    """Return the sales tax percent for a region as a Decimal percent_number (8.25 means 8.25%).

    region None (unknown customer) gives 0. An unknown region string raises KeyError.
    """
    if region is None:
        return Decimal("0")
    key = str(region).strip()
    if key not in _RATES:
        raise KeyError(f"no tax rate for region {region!r}")
    return _RATES[key]


def is_exempt(category):
    """True if items in this category are not taxed."""
    return str(category).strip().lower() in _EXEMPT


def compute_tax(region, taxable_lines, discount_pct):
    """Compute the sales tax for one order as a Decimal dollar amount rounded to the cent.

    Arguments:
        region: region string such as "TX" (from pricing.get_customer(id)["region"]),
                or None for an unknown customer (tax is 0.00).
        taxable_lines: iterable of (category, amount) pairs for ALL order lines. amount is
                Decimal dollars. Lines whose category is exempt are dropped here.
        discount_pct: customer discount as a percent number (10 means 10%). Use 0 for none.

    Rule (RULES.md):
        taxable = sum of non-exempt line amounts
        base    = taxable * (100 - discount_pct) / 100
        tax     = base * tax_pct / 100, rounded half up to the cent

    Raises:
        KeyError: region is a string that is not in data_tax/rates.csv.
        TypeError / ValueError: bad input types or a discount outside 0..100.
    """
    discount = _to_decimal(discount_pct, "discount_pct")
    if discount < 0 or discount > _HUNDRED:
        raise ValueError(f"discount_pct must be between 0 and 100, got {discount_pct!r}")

    taxable = Decimal("0")
    for category, amount in taxable_lines:
        if is_exempt(category):
            continue
        taxable += _to_decimal(amount, "line amount")

    if region is None:
        return _ZERO_CENTS

    tax_pct = rate_pct(region)  # raises KeyError for unknown regions
    base = taxable * (_HUNDRED - discount) / _HUNDRED
    tax = base * tax_pct / _HUNDRED
    return tax.quantize(_CENT, rounding=ROUND_HALF_UP)
