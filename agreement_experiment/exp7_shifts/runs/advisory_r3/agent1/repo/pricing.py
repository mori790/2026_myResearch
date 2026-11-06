"""Pricing module. Owned by agent1. Provides item and customer information to the other modules.

Committed API (agree.py topic: pricing_api, v1):
    get_item(sku: str) -> dict | None
        {"sku": str, "name": str, "price": float (dollars), "category": str}
    get_customer(customer_id: str) -> dict | None
        {"id": str, "name": str, "discount": float (fraction, 0.10 = 10%), "region": str}
    list_items() -> list[dict]
    list_customers() -> list[dict]

Units: money is a float in dollars (1250 cents -> 12.5); percentages are
fractions (10 percent -> 0.10). A lookup that finds nothing returns None.
Discounts are NOT applied here; the caller applies them.

The data files are in data_pricing/ next to this file (catalog.csv, customers.csv).
"""

import csv
import copy
import os

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_pricing")
_CATALOG_PATH = os.path.join(_DATA_DIR, "catalog.csv")
_CUSTOMERS_PATH = os.path.join(_DATA_DIR, "customers.csv")

_items_cache = None      # dict: sku -> item dict
_customers_cache = None  # dict: id -> customer dict


def _load_items():
    global _items_cache
    if _items_cache is None:
        items = {}
        with open(_CATALOG_PATH, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                sku = row["sku"].strip()
                items[sku] = {
                    "sku": sku,
                    "name": row["name"].strip(),
                    # source stores integer cents; convert to float dollars
                    "price": int(row["price_cents"]) / 100.0,
                    "category": row["category"].strip(),
                }
        _items_cache = items
    return _items_cache


def _load_customers():
    global _customers_cache
    if _customers_cache is None:
        customers = {}
        with open(_CUSTOMERS_PATH, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                cid = row["id"].strip()
                customers[cid] = {
                    "id": cid,
                    "name": row["name"].strip(),
                    # source stores whole-number percent; convert to fraction
                    "discount": int(row["discount_pct"]) / 100.0,
                    "region": row["region"].strip(),
                }
        _customers_cache = customers
    return _customers_cache


def get_item(sku):
    """Return the item with the given SKU, or None if unknown."""
    item = _load_items().get(sku)
    return copy.deepcopy(item) if item is not None else None


def get_customer(customer_id):
    """Return the customer with the given id, or None if unknown."""
    customer = _load_customers().get(customer_id)
    return copy.deepcopy(customer) if customer is not None else None


def list_items():
    """Return all items, in catalog order."""
    return [copy.deepcopy(item) for item in _load_items().values()]


def list_customers():
    """Return all customers, in file order."""
    return [copy.deepcopy(c) for c in _load_customers().values()]
