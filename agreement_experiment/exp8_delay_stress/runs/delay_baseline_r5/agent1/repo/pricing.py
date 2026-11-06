"""Pricing module. Owned by agent1. Provides item and customer information to the other modules.
The data files are in data_pricing/ next to this file.

Conventions (team standard):
- Money amounts are floats in dollars (12.5 means $12.50).
- Percentages are fractions (10% is 0.10).
- A lookup that finds nothing returns None.

Public API:
- get_item(sku)            -> dict {sku, name, price, category} or None
- get_customer(customer_id) -> dict {id, name, discount, region} or None
"""

import csv
import os

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_pricing")
_CATALOG_PATH = os.path.join(_DATA_DIR, "catalog.csv")
_CUSTOMERS_PATH = os.path.join(_DATA_DIR, "customers.csv")

_items = None      # dict: sku -> item dict
_customers = None  # dict: customer id -> customer dict


def _load_items():
    items = {}
    with open(_CATALOG_PATH, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            sku = row["sku"].strip()
            items[sku] = {
                "sku": sku,
                "name": row["name"].strip(),
                # Source data is in cents (integer); convert to dollars (float).
                "price": round(int(row["price_cents"]) / 100, 2),
                "category": row["category"].strip(),
            }
    return items


def _load_customers():
    customers = {}
    with open(_CUSTOMERS_PATH, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            cid = row["id"].strip()
            customers[cid] = {
                "id": cid,
                "name": row["name"].strip(),
                # Source data is a percentage (e.g. 10); convert to a fraction (0.10).
                "discount": round(float(row["discount_pct"]) / 100, 4),
                "region": row["region"].strip(),
            }
    return customers


def _get_items():
    global _items
    if _items is None:
        _items = _load_items()
    return _items


def _get_customers():
    global _customers
    if _customers is None:
        _customers = _load_customers()
    return _customers


def get_item(sku):
    """Return item info for `sku` as a dict, or None if the SKU is unknown.

    price is in dollars (float); category is a string.
    """
    item = _get_items().get(sku)
    return dict(item) if item is not None else None


def get_customer(customer_id):
    """Return customer info for `customer_id` as a dict, or None if unknown.

    discount is a fraction (0.10 means 10%); region is a string.
    """
    customer = _get_customers().get(customer_id)
    return dict(customer) if customer is not None else None
