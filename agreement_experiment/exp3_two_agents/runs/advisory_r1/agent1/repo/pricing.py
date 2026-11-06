"""Pricing module. Owned by agent1 (the pricing developer).

invoice.py (written by agent2) imports this module to get everything it needs
about items and customers. The data files are in data/ next to this file.

API (committed as PRICING_API):
    get_unit_price_cents(sku) -> int | None
        Unit price in integer cents, or None if the SKU is unknown.
    get_customer(customer_id) -> dict | None
        {"name": str, "discount_percent": Decimal, "tax_percent": Decimal}
        or None if the customer is unknown. tax_percent is looked up from
        the customer's region in tax.csv.
"""

import csv
import os
from decimal import Decimal

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

_catalog = None
_customers = None


def _read_rows(filename):
    path = os.path.join(_DATA_DIR, filename)
    with open(path, newline="", encoding="utf-8") as f:
        return [{k: v.strip() for k, v in row.items()} for row in csv.DictReader(f)]


def _load():
    global _catalog, _customers
    if _catalog is not None:
        return

    catalog = {}
    for row in _read_rows("catalog.csv"):
        catalog[row["sku"]] = int(row["price_cents"])

    tax = {}
    for row in _read_rows("tax.csv"):
        tax[row["region"]] = Decimal(row["tax_pct"])

    customers = {}
    for row in _read_rows("customers.csv"):
        region = row["region"]
        if region not in tax:
            raise ValueError(
                f"customer {row['id']} has region {region!r} not found in tax.csv"
            )
        customers[row["id"]] = {
            "name": row["name"],
            "discount_percent": Decimal(row["discount_pct"]),
            "tax_percent": tax[region],
        }

    _catalog = catalog
    _customers = customers


def get_unit_price_cents(sku):
    """Return the unit price in integer cents for sku, or None if unknown."""
    _load()
    return _catalog.get(sku)


def get_customer(customer_id):
    """Return the customer's info dict, or None if the customer is unknown."""
    _load()
    customer = _customers.get(customer_id)
    if customer is None:
        return None
    return dict(customer)
