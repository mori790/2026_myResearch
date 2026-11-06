"""Pricing module. Owned by agent1 (the pricing developer).

invoice.py (written by agent2) imports this module to get everything it needs
about items and customers. The data files are in data/ next to this file.

API (agreed with agent2):
    get_unit_price_cents(sku) -> int | None
        Unit price in integer cents, or None if the sku is unknown.
    get_customer(customer_id) -> dict | None
        None if the customer is unknown. Otherwise a dict with:
            "name":         str
            "discount_pct": Decimal (e.g. Decimal("10"))
            "tax_pct":      Decimal (tax rate of the customer's region,
                            e.g. Decimal("8.25"))

Money is integer cents and percentages are Decimal, so no float rounding is
involved here. Rounding of discount and tax amounts to cents is done by
invoice.py.
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
    catalog = {}
    for row in _read_rows("catalog.csv"):
        catalog[row["sku"]] = int(row["price_cents"])
    return catalog


def _load_tax():
    tax = {}
    for row in _read_rows("tax.csv"):
        tax[row["region"]] = Decimal(row["tax_pct"])
    return tax


def _load_customers(tax):
    customers = {}
    for row in _read_rows("customers.csv"):
        region = row["region"]
        if region not in tax:
            raise ValueError(
                f"customer {row['id']} has region {region!r} "
                "which is missing from tax.csv"
            )
        customers[row["id"]] = {
            "name": row["name"],
            "discount_pct": Decimal(row["discount_pct"]),
            "tax_pct": tax[region],
        }
    return customers


_CATALOG = _load_catalog()
_TAX = _load_tax()
_CUSTOMERS = _load_customers(_TAX)


def get_unit_price_cents(sku):
    """Return the unit price of `sku` in cents, or None if unknown."""
    return _CATALOG.get(sku)


def get_customer(customer_id):
    """Return the customer's info as a dict, or None if unknown.

    The returned dict is a copy, so callers cannot change the loaded data.
    """
    customer = _CUSTOMERS.get(customer_id)
    if customer is None:
        return None
    return dict(customer)
