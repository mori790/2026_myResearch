"""Pricing module. Owned by agent1. Provides item and customer information to the other modules.
The data files are in data_pricing/ next to this file.

Conventions (team standard):
- Money amounts are floats in dollars (1250 cents -> 12.5).
- Percentages are fractions (10 percent -> 0.10).
- A lookup that finds nothing returns None.

Public API:
- get_item(sku)            -> dict {"sku", "name", "price", "category"} or None
- get_price(sku)           -> float (dollars) or None
- get_customer(customer_id) -> dict {"id", "name", "discount", "region"} or None
- list_items()             -> list of item dicts (catalog order)
- list_customers()         -> list of customer dicts (file order)

All returned dicts are fresh copies; mutating them does not affect the data.
"""

import csv
import os

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_pricing")
_CATALOG_PATH = os.path.join(_DATA_DIR, "catalog.csv")
_CUSTOMERS_PATH = os.path.join(_DATA_DIR, "customers.csv")

_items = None      # dict: sku -> item dict (insertion order = catalog order)
_customers = None  # dict: customer id -> customer dict (insertion order = file order)


def _load_items(path=_CATALOG_PATH):
    items = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            sku = row["sku"].strip()
            if sku in items:
                raise ValueError(f"duplicate sku {sku!r} in {path}")
            cents = int(row["price_cents"])
            items[sku] = {
                "sku": sku,
                "name": row["name"].strip(),
                "price": cents / 100.0,  # cents -> dollars
                "category": row["category"].strip(),
            }
    return items


def _load_customers(path=_CUSTOMERS_PATH):
    customers = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            cid = row["id"].strip()
            if cid in customers:
                raise ValueError(f"duplicate customer id {cid!r} in {path}")
            pct = float(row["discount_pct"])
            customers[cid] = {
                "id": cid,
                "name": row["name"].strip(),
                "discount": round(pct / 100.0, 6),  # percent -> fraction
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
    """Return the item with this SKU as a dict, or None if not found."""
    item = _get_items().get(sku)
    return dict(item) if item is not None else None


def get_price(sku):
    """Return the unit price in dollars for this SKU, or None if not found."""
    item = _get_items().get(sku)
    return item["price"] if item is not None else None


def get_customer(customer_id):
    """Return the customer with this id as a dict, or None if not found.

    "discount" is a fraction (0.10 means 10 percent off).
    """
    customer = _get_customers().get(customer_id)
    return dict(customer) if customer is not None else None


def list_items():
    """Return all items (catalog order) as a list of dicts."""
    return [dict(item) for item in _get_items().values()]


def list_customers():
    """Return all customers (file order) as a list of dicts."""
    return [dict(c) for c in _get_customers().values()]
