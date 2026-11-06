"""Pricing module. Owned by agent1. Provides item and customer information to the other modules.
The data files are in data_pricing/ next to this file.

Team conventions (decision PRICING_API v1, committed):
  - Money amounts are floats in dollars (12.5 means $12.50).
  - Percentages are fractions (10% is 0.10).
  - A lookup that finds nothing returns None.

Public API:
  get_item(sku)          -> dict or None
      {"sku": str, "name": str, "price": float (dollars), "category": str}
  get_customer(cust_id)  -> dict or None
      {"id": str, "name": str, "discount": float (fraction, e.g. 0.10), "region": str}
  list_items()           -> list of item dicts (catalog order)
  list_customers()       -> list of customer dicts (file order)

All returned dicts are fresh copies, so callers cannot modify the internal data.
"""

import csv
import os

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_pricing")
_CATALOG_PATH = os.path.join(_DATA_DIR, "catalog.csv")
_CUSTOMERS_PATH = os.path.join(_DATA_DIR, "customers.csv")


def _load_catalog(path):
    items = []
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            items.append({
                "sku": row["sku"].strip(),
                "name": row["name"].strip(),
                # Stored in cents in the file; converted to dollars here.
                "price": round(int(row["price_cents"].strip()) / 100, 2),
                "category": row["category"].strip(),
            })
    return items


def _load_customers(path):
    customers = []
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            customers.append({
                "id": row["id"].strip(),
                "name": row["name"].strip(),
                # Stored as a percentage in the file (10 means 10%); converted to a fraction here.
                "discount": round(float(row["discount_pct"].strip()) / 100, 4),
                "region": row["region"].strip(),
            })
    return customers


_ITEMS = _load_catalog(_CATALOG_PATH)
_ITEMS_BY_SKU = {item["sku"]: item for item in _ITEMS}

_CUSTOMERS = _load_customers(_CUSTOMERS_PATH)
_CUSTOMERS_BY_ID = {cust["id"]: cust for cust in _CUSTOMERS}


def get_item(sku):
    """Return the catalog entry for `sku`, or None if no such item exists."""
    item = _ITEMS_BY_SKU.get(sku)
    return dict(item) if item is not None else None


def get_customer(cust_id):
    """Return the customer record for `cust_id`, or None if no such customer exists."""
    cust = _CUSTOMERS_BY_ID.get(cust_id)
    return dict(cust) if cust is not None else None


def list_items():
    """Return all catalog items in catalog order."""
    return [dict(item) for item in _ITEMS]


def list_customers():
    """Return all customers in file order."""
    return [dict(cust) for cust in _CUSTOMERS]
