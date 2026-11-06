"""Pricing module. Owned by agent1. Provides item and customer information to the other modules.
The data files are in data_pricing/ next to this file.

Team conventions (see the decision log, topic "pricing-api"):
  - Money amounts are floats in dollars (12.5 means $12.50).
  - Percentages are fractions (10% is 0.10).
  - A lookup that finds nothing returns None.

Public API:
  get_item(sku)          -> dict {"sku", "name", "price", "category"} or None
  get_customer(cust_id)  -> dict {"id", "name", "discount", "region"} or None
  list_items()           -> list of item dicts, in catalog order
  list_customers()       -> list of customer dicts, in file order

All functions return fresh copies, so callers may modify the results freely.
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
                # catalog stores integer cents; convert to float dollars
                "price": round(int(row["price_cents"]) / 100, 2),
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
                # file stores percent (10 means 10%); convert to fraction (0.10)
                "discount": round(float(row["discount_pct"]) / 100, 6),
                "region": row["region"].strip(),
            })
    return customers


# Loaded once at import time; the data files are small.
_ITEMS = _load_items()
_ITEMS_BY_SKU = {item["sku"]: item for item in _ITEMS}
_CUSTOMERS = _load_customers()
_CUSTOMERS_BY_ID = {c["id"]: c for c in _CUSTOMERS}


def get_item(sku):
    """Return the item with the given SKU as a dict, or None if it does not exist."""
    item = _ITEMS_BY_SKU.get(sku)
    return dict(item) if item is not None else None


def get_customer(cust_id):
    """Return the customer with the given id as a dict, or None if it does not exist."""
    customer = _CUSTOMERS_BY_ID.get(cust_id)
    return dict(customer) if customer is not None else None


def list_items():
    """Return all catalog items as a list of dicts, in catalog order."""
    return [dict(item) for item in _ITEMS]


def list_customers():
    """Return all customers as a list of dicts, in file order."""
    return [dict(c) for c in _CUSTOMERS]
