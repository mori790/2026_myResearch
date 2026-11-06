"""Pricing module. Owned by agent1. Provides item and customer information to the other modules.
The data files are in data_pricing/ next to this file.

Team conventions (see the agreed API):
  * Money amounts are floats in dollars (1250 cents -> 12.5).
  * Percentages are fractions (10 -> 0.10).
  * A lookup that finds nothing returns None.

Public API:
  get_item(sku)            -> dict {"sku", "name", "price", "category"} or None
  get_customer(customer_id)-> dict {"id", "name", "discount_pct", "region"} or None
  list_items()             -> list of item dicts, in catalog order
  list_customers()         -> list of customer dicts, in file order
"""

import csv
import os

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_pricing")
_CATALOG_PATH = os.path.join(_DATA_DIR, "catalog.csv")
_CUSTOMERS_PATH = os.path.join(_DATA_DIR, "customers.csv")


def _load_items(path):
    items = []
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            cents = int(row["price_cents"].strip())
            items.append({
                "sku": row["sku"].strip(),
                "name": row["name"].strip(),
                "price": round(cents / 100, 2),  # dollars, float
                "category": row["category"].strip(),
            })
    return items


def _load_customers(path):
    customers = []
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            pct = float(row["discount_pct"].strip())
            customers.append({
                "id": row["id"].strip(),
                "name": row["name"].strip(),
                "discount_pct": round(pct / 100, 6),  # fraction, e.g. 10 -> 0.10
                "region": row["region"].strip(),
            })
    return customers


_ITEMS = _load_items(_CATALOG_PATH)
_CUSTOMERS = _load_customers(_CUSTOMERS_PATH)
_ITEMS_BY_SKU = {item["sku"]: item for item in _ITEMS}
_CUSTOMERS_BY_ID = {c["id"]: c for c in _CUSTOMERS}


def get_item(sku):
    """Return a copy of the item dict for `sku`, or None if the SKU is unknown."""
    item = _ITEMS_BY_SKU.get(sku)
    return dict(item) if item is not None else None


def get_customer(customer_id):
    """Return a copy of the customer dict for `customer_id`, or None if unknown."""
    customer = _CUSTOMERS_BY_ID.get(customer_id)
    return dict(customer) if customer is not None else None


def list_items():
    """Return copies of all catalog items, in catalog order."""
    return [dict(item) for item in _ITEMS]


def list_customers():
    """Return copies of all customers, in file order."""
    return [dict(c) for c in _CUSTOMERS]
