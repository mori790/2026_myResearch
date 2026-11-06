"""Pricing module. Owned by agent1. Provides item and customer information to the other modules.
The data files are in data_pricing/ next to this file.

API (pricing_api v1):
    get_item(sku)                -> dict {sku, name, price, category} or None
    get_customer(customer_id)    -> dict {id, name, discount, region} or None
    all_items()                  -> list of item dicts
    all_customers()              -> list of customer dicts

Conventions (team standard):
    * Money amounts are floats in dollars (price 12.5 means $12.50).
    * Percentages are fractions (discount 10% is 0.10).
    * A lookup that finds nothing returns None.
"""

import csv
import os

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_pricing")
_CATALOG_PATH = os.path.join(_DATA_DIR, "catalog.csv")
_CUSTOMERS_PATH = os.path.join(_DATA_DIR, "customers.csv")

_items = None      # dict: sku -> item dict, loaded lazily
_customers = None  # dict: customer id -> customer dict, loaded lazily


def _load_items():
    global _items
    if _items is None:
        loaded = {}
        with open(_CATALOG_PATH, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                sku = row["sku"].strip()
                loaded[sku] = {
                    "sku": sku,
                    "name": row["name"].strip(),
                    # catalog stores integer cents; convert to float dollars
                    "price": int(row["price_cents"]) / 100,
                    "category": row["category"].strip(),
                }
        _items = loaded
    return _items


def _load_customers():
    global _customers
    if _customers is None:
        loaded = {}
        with open(_CUSTOMERS_PATH, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                cid = row["id"].strip()
                loaded[cid] = {
                    "id": cid,
                    "name": row["name"].strip(),
                    # discount_pct stores a percentage (10 means 10%); convert to fraction
                    "discount": float(row["discount_pct"]) / 100,
                    "region": row["region"].strip(),
                }
        _customers = loaded
    return _customers


def get_item(sku):
    """Return the item with the given SKU as a dict, or None if it does not exist."""
    item = _load_items().get(sku)
    return dict(item) if item is not None else None


def get_customer(customer_id):
    """Return the customer with the given id as a dict, or None if it does not exist."""
    customer = _load_customers().get(customer_id)
    return dict(customer) if customer is not None else None


def all_items():
    """Return a list of all items (dicts in the same shape as get_item)."""
    return [dict(item) for item in _load_items().values()]


def all_customers():
    """Return a list of all customers (dicts in the same shape as get_customer)."""
    return [dict(customer) for customer in _load_customers().values()]
