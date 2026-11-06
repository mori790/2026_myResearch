"""Pricing module. Owned by agent1 (the pricing developer).

invoice.py (written by agent2) imports this module to get everything it needs
about items and customers. The data files are in data/ next to this file.

API (committed as agree.py decision "pricing_api" v1):
    get_unit_price(sku) -> Decimal | None
        Unit price in dollars, e.g. Decimal('12.50'). None if the sku is unknown.
    get_customer(customer_id) -> dict | None
        {'name': str, 'discount_percent': Decimal, 'tax_percent': Decimal}
        or None if the customer id is unknown. Percents are Decimal, e.g.
        Decimal('8.25') means 8.25%. tax_percent is looked up from the
        customer's region in tax.csv; if the region is not listed there,
        tax_percent is Decimal('0').

All money and percentages are Decimal parsed from the data files (never floats).
Rounding is not done here; invoice.py handles it.
"""

import csv
import os
from decimal import Decimal

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")


def _read_rows(filename):
    path = os.path.join(_DATA_DIR, filename)
    with open(path, newline="", encoding="utf-8") as f:
        return [
            {key.strip(): (value or "").strip() for key, value in row.items()}
            for row in csv.DictReader(f)
        ]


def _load_catalog():
    # price_cents is an integer number of cents; scaleb(-2) divides by 100 exactly.
    return {
        row["sku"]: Decimal(row["price_cents"]).scaleb(-2)
        for row in _read_rows("catalog.csv")
    }


def _load_tax():
    return {
        row["region"]: Decimal(row["tax_pct"])
        for row in _read_rows("tax.csv")
    }


def _load_customers():
    return {
        row["id"]: {
            "name": row["name"],
            "discount_percent": Decimal(row["discount_pct"]),
            "region": row["region"],
        }
        for row in _read_rows("customers.csv")
    }


_CATALOG = _load_catalog()
_TAX = _load_tax()
_CUSTOMERS = _load_customers()


def get_unit_price(sku):
    """Return the unit price of `sku` in dollars as Decimal, or None if unknown."""
    return _CATALOG.get(sku)


def get_customer(customer_id):
    """Return customer info as a dict, or None if the customer id is unknown."""
    customer = _CUSTOMERS.get(customer_id)
    if customer is None:
        return None
    return {
        "name": customer["name"],
        "discount_percent": customer["discount_percent"],
        "tax_percent": _TAX.get(customer["region"], Decimal("0")),
    }
