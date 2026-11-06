"""Pricing module. Owned by agent1. Provides item and customer information to the other modules.
The data files are in data_pricing/ next to this file.

API (agreed as `pricing_api`):
    get_item(sku) -> dict | None
        {"sku": str, "name": str, "price": float, "category": str}
        price is in dollars (12.5 means $12.50). None if the SKU is unknown.
    get_customer(customer_id) -> dict | None
        {"id": str, "name": str, "discount": float, "region": str}
        discount is a fraction (0.10 means 10%). None if the ID is unknown.
    list_items() -> list[dict]       all items, in catalog order, same shape as get_item
    list_customers() -> list[dict]   all customers, same shape as get_customer

pricing.py computes no tax. region is passed through unchanged for tax.py.
"""

import csv
import os

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_pricing")
_CATALOG_PATH = os.path.join(_DATA_DIR, "catalog.csv")
_CUSTOMERS_PATH = os.path.join(_DATA_DIR, "customers.csv")


def _load_items():
    items = []
    with open(_CATALOG_PATH, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            items.append({
                "sku": row["sku"].strip(),
                "name": row["name"].strip(),
                # price_cents is an integer number of cents; convert to dollars.
                "price": int(row["price_cents"]) / 100,
                "category": row["category"].strip(),
            })
    return items


def _load_customers():
    customers = []
    with open(_CUSTOMERS_PATH, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            customers.append({
                "id": row["id"].strip(),
                "name": row["name"].strip(),
                # discount_pct is a percentage (10 means 10%); convert to a fraction.
                "discount": float(row["discount_pct"]) / 100,
                "region": row["region"].strip(),
            })
    return customers


_ITEMS = _load_items()
_CUSTOMERS = _load_customers()
_ITEMS_BY_SKU = {item["sku"]: item for item in _ITEMS}
_CUSTOMERS_BY_ID = {c["id"]: c for c in _CUSTOMERS}


def get_item(sku):
    """Return the item with the given SKU as a dict, or None if unknown."""
    item = _ITEMS_BY_SKU.get(sku)
    return dict(item) if item is not None else None


def get_customer(customer_id):
    """Return the customer with the given ID as a dict, or None if unknown."""
    customer = _CUSTOMERS_BY_ID.get(customer_id)
    return dict(customer) if customer is not None else None


def list_items():
    """Return all items in catalog order."""
    return [dict(item) for item in _ITEMS]


def list_customers():
    """Return all customers in file order."""
    return [dict(c) for c in _CUSTOMERS]
