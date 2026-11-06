"""Pricing module. Owned by agent1. Provides item and customer information to the other modules.
The data files are in data_pricing/ next to this file.

Conventions (team standard):
- Money amounts are floats in dollars (12.5 means $12.50).
- Percentages are fractions (10% is 0.10).
- A lookup that finds nothing returns None.

Public API:
- get_item(sku) -> dict or None
    keys: "sku" (str), "name" (str), "price" (float, dollars), "category" (str)
- get_price(sku) -> float (dollars) or None
- get_customer(customer_id) -> dict or None
    keys: "id" (str), "name" (str), "discount" (float fraction, 0.10 = 10%), "region" (str)
- list_items() -> list of item dicts (catalog order)
- list_customers() -> list of customer dicts (file order)
"""

import csv
import os

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_pricing")
_CATALOG_PATH = os.path.join(_DATA_DIR, "catalog.csv")
_CUSTOMERS_PATH = os.path.join(_DATA_DIR, "customers.csv")


def _load_catalog(path):
    items = {}
    order = []
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            sku = row["sku"].strip()
            item = {
                "sku": sku,
                "name": row["name"].strip(),
                # Source data stores cents as integers; convert to dollars.
                "price": int(row["price_cents"]) / 100.0,
                "category": row["category"].strip(),
            }
            items[sku] = item
            order.append(sku)
    return items, order


def _load_customers(path):
    customers = {}
    order = []
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            cid = row["id"].strip()
            customer = {
                "id": cid,
                "name": row["name"].strip(),
                # Source data stores percentages as whole numbers; convert to fractions.
                "discount": int(row["discount_pct"]) / 100.0,
                "region": row["region"].strip(),
            }
            customers[cid] = customer
            order.append(cid)
    return customers, order


_ITEMS, _ITEM_ORDER = _load_catalog(_CATALOG_PATH)
_CUSTOMERS, _CUSTOMER_ORDER = _load_customers(_CUSTOMERS_PATH)


def get_item(sku):
    """Return a copy of the item dict for `sku`, or None if unknown."""
    item = _ITEMS.get(sku)
    return dict(item) if item is not None else None


def get_price(sku):
    """Return the unit price in dollars for `sku`, or None if unknown."""
    item = _ITEMS.get(sku)
    return item["price"] if item is not None else None


def get_customer(customer_id):
    """Return a copy of the customer dict for `customer_id`, or None if unknown."""
    customer = _CUSTOMERS.get(customer_id)
    return dict(customer) if customer is not None else None


def list_items():
    """Return copies of all item dicts in catalog order."""
    return [dict(_ITEMS[sku]) for sku in _ITEM_ORDER]


def list_customers():
    """Return copies of all customer dicts in file order."""
    return [dict(_CUSTOMERS[cid]) for cid in _CUSTOMER_ORDER]
