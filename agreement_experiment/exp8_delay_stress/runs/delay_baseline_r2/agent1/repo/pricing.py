"""Pricing module. Owned by agent1. Provides item and customer information to the other modules.
The data files are in data_pricing/ next to this file.

Conventions (team standard):
  * Money amounts are floats in dollars (12.5 means $12.50).
  * Percentages are fractions (10% is 0.10).
  * A lookup that finds nothing returns None.

Public API:
  get_item(sku)            -> dict | None   keys: sku, name, price, category
  get_customer(customer_id)-> dict | None   keys: id, name, discount, region
  list_items()             -> list[dict]
  list_customers()         -> list[dict]

Every call returns fresh copies, so callers cannot modify the loaded data.
"""

import csv
import os

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_pricing")
_CATALOG_PATH = os.path.join(_DATA_DIR, "catalog.csv")
_CUSTOMERS_PATH = os.path.join(_DATA_DIR, "customers.csv")


def _load_items(path):
    """catalog.csv columns: sku,name,price_cents,category (price is integer cents)."""
    items = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            sku = row["sku"].strip()
            items[sku] = {
                "sku": sku,
                "name": row["name"].strip(),
                # cents -> dollars; int() first so the value is exactly the stored cents
                "price": int(row["price_cents"].strip()) / 100,
                "category": row["category"].strip(),
            }
    return items


def _load_customers(path):
    """customers.csv columns: id,name,discount_pct,region (discount is whole percent)."""
    customers = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            cid = row["id"].strip()
            customers[cid] = {
                "id": cid,
                "name": row["name"].strip(),
                # percent -> fraction, e.g. 10 -> 0.10
                "discount": int(row["discount_pct"].strip()) / 100,
                "region": row["region"].strip(),
            }
    return customers


_ITEMS = _load_items(_CATALOG_PATH)
_CUSTOMERS = _load_customers(_CUSTOMERS_PATH)


def get_item(sku):
    """Return item info for `sku` as a dict, or None if the SKU is unknown."""
    item = _ITEMS.get(sku)
    return dict(item) if item is not None else None


def get_customer(customer_id):
    """Return customer info for `customer_id` as a dict, or None if unknown."""
    customer = _CUSTOMERS.get(customer_id)
    return dict(customer) if customer is not None else None


def list_items():
    """Return all catalog items as a list of dicts (copies)."""
    return [dict(item) for item in _ITEMS.values()]


def list_customers():
    """Return all customers as a list of dicts (copies)."""
    return [dict(customer) for customer in _CUSTOMERS.values()]
