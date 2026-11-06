"""Pricing module. Owned by agent1. Provides item and customer information to the other modules.
The data files are in data_pricing/ next to this file.

Interface (committed decision pricing_api v2):
    get_item(sku)             -> {"sku": str, "name": str, "price_cents": int, "category": str} or None
    get_customer(customer_id) -> {"id": str, "name": str, "discount_pct": number, "region": str} or None

Conventions:
    - price_cents is the unit price in integer cents (1250 means $12.50), before any customer discount.
    - discount_pct is a percent number (10 means 10%), not a fraction.
    - A lookup that finds nothing returns None.
"""

import csv
import os

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_pricing")
_CATALOG_PATH = os.path.join(_DATA_DIR, "catalog.csv")
_CUSTOMERS_PATH = os.path.join(_DATA_DIR, "customers.csv")


def _load_items(path):
    items = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            sku = row["sku"].strip()
            items[sku] = {
                "sku": sku,
                "name": row["name"].strip(),
                "price_cents": int(row["price_cents"]),
                "category": row["category"].strip(),
            }
    return items


def _load_customers(path):
    customers = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            cid = row["id"].strip()
            customers[cid] = {
                "id": cid,
                "name": row["name"].strip(),
                "discount_pct": int(row["discount_pct"]),
                "region": row["region"].strip(),
            }
    return customers


_ITEMS = _load_items(_CATALOG_PATH)
_CUSTOMERS = _load_customers(_CUSTOMERS_PATH)


def get_item(sku):
    """Return the item with this SKU as a dict copy, or None if the SKU is unknown."""
    item = _ITEMS.get(sku)
    return dict(item) if item is not None else None


def get_customer(customer_id):
    """Return the customer with this id as a dict copy, or None if the id is unknown."""
    customer = _CUSTOMERS.get(customer_id)
    return dict(customer) if customer is not None else None
