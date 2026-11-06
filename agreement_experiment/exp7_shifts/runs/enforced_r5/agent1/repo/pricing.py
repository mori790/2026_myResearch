"""Pricing module. Owned by agent1. Provides item and customer information to the other modules.

The data files are in data_pricing/ next to this file.

Team conventions (followed here):
  * Money amounts are floats in dollars (12.5 means $12.50).
  * Percentages are fractions (10% is 0.10).
  * A lookup that finds nothing returns None.

Public API (committed decision "pricing-api" v1):
  get_item(sku)             -> dict or None
      keys: "sku" (str), "name" (str), "price" (float, dollars), "category" (str)
  get_customer(customer_id) -> dict or None
      keys: "id" (str), "name" (str), "discount" (float fraction, e.g. 0.10),
            "region" (str, e.g. "TX")
  list_items()              -> list of item dicts, in file order
  list_customers()          -> list of customer dicts, in file order

The functions return fresh copies, so callers may modify the returned dicts safely.
"""

import csv
import os

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_pricing")
_CATALOG_PATH = os.path.join(_DATA_DIR, "catalog.csv")
_CUSTOMERS_PATH = os.path.join(_DATA_DIR, "customers.csv")


def _load_items(path):
    """Read catalog.csv. Raw price_cents (int) becomes price (float, dollars)."""
    items = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            sku = row["sku"].strip()
            items[sku] = {
                "sku": sku,
                "name": row["name"].strip(),
                "price": int(row["price_cents"].strip()) / 100,
                "category": row["category"].strip(),
            }
    return items


def _load_customers(path):
    """Read customers.csv. Raw discount_pct (int, percent) becomes discount (float fraction)."""
    customers = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            cid = row["id"].strip()
            customers[cid] = {
                "id": cid,
                "name": row["name"].strip(),
                "discount": int(row["discount_pct"].strip()) / 100,
                "region": row["region"].strip(),
            }
    return customers


_ITEMS = _load_items(_CATALOG_PATH)
_CUSTOMERS = _load_customers(_CUSTOMERS_PATH)


def get_item(sku):
    """Return the item with the given SKU as a dict, or None if it does not exist."""
    item = _ITEMS.get(sku)
    return dict(item) if item is not None else None


def get_customer(customer_id):
    """Return the customer with the given ID as a dict, or None if it does not exist."""
    customer = _CUSTOMERS.get(customer_id)
    return dict(customer) if customer is not None else None


def list_items():
    """Return all items (list of dicts) in catalog file order."""
    return [dict(item) for item in _ITEMS.values()]


def list_customers():
    """Return all customers (list of dicts) in customer file order."""
    return [dict(customer) for customer in _CUSTOMERS.values()]
