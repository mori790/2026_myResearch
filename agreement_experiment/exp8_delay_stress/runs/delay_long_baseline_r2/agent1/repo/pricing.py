"""Pricing module. Owned by agent1. Provides item and customer information to the other modules.
The data files are in data_pricing/ next to this file.

Public API (team convention: money in dollars as float, percentages as fractions, lookup miss -> None):

    get_item(sku) -> dict or None
        keys: sku (str), name (str), price (float, dollars), category (str)

    get_customer(customer_id) -> dict or None
        keys: id (str), name (str), discount (float, fraction: 0.10 means 10%), region (str)

    list_items() -> list of dict        # all items, same shape as get_item, catalog order
    list_customers() -> list of dict    # all customers, same shape as get_customer, file order

Returned dicts are copies; mutating them does not affect the module's data.
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
                # Source stores integer cents; convert to float dollars.
                "price": int(row["price_cents"].strip()) / 100.0,
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
                # Source stores integer percent; convert to fraction.
                "discount": int(row["discount_pct"].strip()) / 100.0,
                "region": row["region"].strip(),
            }
    return customers


_ITEMS = _load_items(_CATALOG_PATH)
_CUSTOMERS = _load_customers(_CUSTOMERS_PATH)


def get_item(sku):
    """Return item info for `sku` as a dict, or None if unknown."""
    item = _ITEMS.get(sku)
    return dict(item) if item is not None else None


def get_customer(customer_id):
    """Return customer info for `customer_id` as a dict, or None if unknown."""
    customer = _CUSTOMERS.get(customer_id)
    return dict(customer) if customer is not None else None


def list_items():
    """Return all items (list of dicts), in catalog order."""
    return [dict(item) for item in _ITEMS.values()]


def list_customers():
    """Return all customers (list of dicts), in file order."""
    return [dict(c) for c in _CUSTOMERS.values()]
